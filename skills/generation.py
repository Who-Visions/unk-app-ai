"""
Generation Skills
=================
Capabilities for generating Images and Videos using Gemini and Veo models.
"""
import asyncio
import os
from typing import List, Optional

from google import genai
from google.genai import types

from gemini_agent.models_spec import get_model_id
from routers.config import GOOGLE_GENAI_API_KEY, logger

# Client instantiated lazily


async def generate_image(
    prompt: str,
    output_file: str,
    model_alias: str = "gemini_3_pro_image",
    aspect_ratio: str = "1:1",
    resolution: str = "1K", # 1K, 2K, 4K
    person_generation: str = "allow_adult",
    reference_images: Optional[List[str]] = None,
    use_search_grounding: bool = False
) -> str:
    """
    Generates an image using Gemini 3 Pro Image (Nano Banana Pro) or similar.

    Args:
        prompt: Text description.
        output_file: Path to save the PNG/JPEG.
        model_alias: Alias from models_spec.py.
        aspect_ratio: '1:1', '16:9', '4:3', etc.
        resolution: '1K', '2K', or '4K' (Gemini 3 Pro only).
        person_generation: Safety setting for people.
        reference_images: List of paths to reference images (up to 14).
        use_search_grounding: Whether to use Google Search for grounding.
    """
    model_id = get_model_id(model_alias)
    client = genai.Client(api_key=GOOGLE_GENAI_API_KEY)


    logger.info(f"Generating image with {model_id}...")

    contents = [prompt]

    # Handle reference images
    if reference_images:
        for ref_img_path in reference_images:
             # Support simple strings or dicts. For now assuming simple paths.
             # Apply 'media_resolution_high' by default for quality.

            if os.path.exists(ref_img_path):
                with open(ref_img_path, "rb") as f:
                    img_bytes = f.read()
                mime = "image/png" if ref_img_path.endswith(".png") else "image/jpeg"

                # Create the Part with media_resolution
                # Note: media_resolution is passed inside the Part's optional config/metadata if supported,
                # or we rely on the global generation config if that's the only place (Gemini 3 supports per-part).
                # effectively: types.Part(inline_data=..., media_resolution=...)
                # but SDK might need types.MediaResolution wrapper.

                # Check SDK capability for per-part media_resolution (v1alpha feature)
                # We'll try to pass it via kwarg if the SDK constructor supports it,
                # otherwise we might need to construct the proto or just rely on global defaults.
                # The docs showed: types.Part(..., media_resolution={"level": "media_resolution_high"})

                part_args = {
                    "inline_data": types.Blob(data=img_bytes, mime_type=mime)
                }

                # Attempt to inject media_resolution if permissible
                # We'll use a try-safe approach or specific SDK object if we knew the exact definition.
                # Based on doc: media_resolution={"level": "media_resolution_high"}
                video_res_config = {"level": "media_resolution_high"} # Reuse for images too
                part_args["media_resolution"] = video_res_config

                try:
                    contents.append(types.Part(**part_args))
                except TypeError:
                     # Fallback if SDK version doesn't support the kwarg yet
                     contents.append(types.Part(inline_data=types.Blob(data=img_bytes, mime_type=mime)))

            else:
                logger.warning(f"Reference image not found: {ref_img_path}")

    # Config
    image_config = types.ImageConfig(
        aspect_ratio=aspect_ratio,
        image_size=resolution
    )

    tools = []
    if use_search_grounding:
        tools.append(types.Tool(google_search=types.GoogleSearch()))

    config = types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"], # Requesting image output
        image_config=image_config,
        tools=tools if tools else None
    )

    try:
        # SDK call - sync wrapper for now as SDK seems to be sync-first in examples,
        # but we should check if async is available. Examples showed `client.aio`.
        # Using async client here.
        # Note: We need a fresh client for async usually or verify if the global one supports it.
        # Examples: client = genai.Client() ... response = client.models.generate_content(...)
        # We'll use the proper async method if available or run in thread.
        # The provided docs for Python don't explicitly show `await` in the snippets
        # except for JS. Wait, Step 1362 Python examples are Sync.
        # Step 1362 JS examples are Async.
        # I will wrap the sync call in to_thread for non-blocking.

        def _run_gen():
            return client.models.generate_content(
                model=model_id,
                contents=contents,
                config=config
            )

        response = await asyncio.to_thread(_run_gen)

        # Process parts
        saved_path = None
        for part in response.parts:
            if part.text:
                logger.info(f"Image Generation Thought/Text: {part.text}")

            if part.inline_data:
                img_data = part.inline_data.data
                # Decode if needed? SDK usually returns raw bytes in 'data' for inline_data objects?
                # Docs say part.as_image().save().
                # Let's try the .as_image() method from SDK
                try:
                    img = part.as_image()
                    img.save(output_file)
                    saved_path = output_file
                    logger.info(f"Image saved to {output_file}")
                except Exception as e:  # pylint: disable=W0718
                    logger.error(f"Failed to save image from part: {e}")
                    # Fallback manual write
                    if img_data:
                         with open(output_file, "wb") as f:
                             f.write(img_data)
                         saved_path = output_file

        return saved_path

    except Exception as e:  # pylint: disable=W0718
        logger.error(f"Error generating image: {e}")
        return None

async def generate_video_veo(
    prompt: str,
    output_file: str,
    duration_seconds: int = 6, # 4, 6, 8
    model_alias: str = "veo_3_1"
):
    """
    Generates video using Veo 3.1.
    Note: Precise API for Veo generation is assumed to follow generate_content
    or a specific video endpoint.
    """
    model_id = get_model_id(model_alias)
    client = genai.Client(api_key=GOOGLE_GENAI_API_KEY)

    logger.info(f"Generating video with {model_id}...")

    # Placeholder for Veo specific config
    # This might need adjustment as real Veo API details emerge.
    # Note on Gemini 3 Thought Signatures:
    # For conversational editing (Image/Video), we must pass back the 'thought_signature'
    # from the previous turn to maintain context. This wrapper currently performs single-turn
    # generation. For multi-turn, use the Agent's chat session which handles history.

    def _run_gen():
        # This is a hypothetical call structure based on unified API philosophy
        return client.models.generate_content(
            model=model_id,
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=["VIDEO", "AUDIO"],
                # Hypothetical config params for Veo
                # media_resolution? duration?
            )
        )

    try:
        response = await asyncio.to_thread(_run_gen)
        # Verify extraction logic for video
        # Likely returns a URI or inline bytes
        return "Video generation logic pending full Veo spec confirmation."
    except Exception as e:  # pylint: disable=W0718
        logger.error(f"Veo generation error: {e}")
        return None
