"""
Generation Skills
=================
Capabilities for generating and editing Images using Gemini 2.5 Flash Image ("Nano Banana")
and Gemini 3 Pro Image ("Nano Banana Pro").
"""
import asyncio
import os
from typing import Any, Dict, List, Optional, Union

from google import genai
from google.genai import types

from gemini_agent.models_spec import get_model_id
from routers.config import GOOGLE_GENAI_API_KEY, logger

# Client instantiated lazily


async def generate_image(
    prompt: str,
    output_file: str,
    model_alias: str = "nano_banana",  # Default to fast/cheap
    aspect_ratio: str = "1:1",
    resolution: str = "1K",  # 1K, 2K, 4K (Pro only)
    reference_images: Optional[List[str]] = None,
    use_search_grounding: bool = False
) -> Optional[str]:
    """
    Generates an image using Gemini Image models.
    """
    model_id = get_model_id(model_alias)
    client = genai.Client(api_key=GOOGLE_GENAI_API_KEY)

    logger.info(f"Generating image with {model_id}...")

    contents = [prompt]

    # Handle reference images (for few-shot or composition)
    if reference_images:
        for ref_img_path in reference_images:
            if os.path.exists(ref_img_path):
                with open(ref_img_path, "rb") as f:
                    img_bytes = f.read()
                mime = "image/png" if ref_img_path.endswith(".png") else "image/jpeg"
                contents.append(types.Part.from_bytes(data=img_bytes, mime_type=mime))
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

    # Thinking config for Pro model
    thinking_config = None
    if "pro" in model_id or "gemini-3" in model_id:
        thinking_config = types.ThinkingConfig(include_thoughts=True)

    config = types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],  # Expecting image output
        image_config=image_config,
        tools=tools if tools else None,
        thinking_config=thinking_config
    )

    try:
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
            if part.thought:
                logger.info(f"Thinking: {part.text[:100]}...")
                continue

            if part.text:
                logger.info(f"Image Gen Text: {part.text}")

            if part.inline_data:
                try:
                    # SDK helper to save image
                    if hasattr(part, 'as_image'):
                        img = part.as_image()
                        img.save(output_file)
                        saved_path = output_file
                        logger.info(f"Image saved to {output_file}")
                    else:
                        # Fallback manual save
                        with open(output_file, "wb") as f:
                            f.write(part.inline_data.data)
                        saved_path = output_file
                except Exception as e:
                    logger.error(f"Failed to save image from part: {e}")

        return saved_path

    except Exception as e:  # pylint: disable=W0718
        logger.error(f"Error generating image: {e}")
        return None


async def edit_image(
    prompt: str,
    input_image_path: str,
    output_file: str,
    model_alias: str = "nano_banana",
    aspect_ratio: str = "1:1"
) -> Optional[str]:
    """
    Edits an image using Gemini (Inpainting/Editing/Style Transfer).
    """
    model_id = get_model_id(model_alias)
    client = genai.Client(api_key=GOOGLE_GENAI_API_KEY)

    logger.info(f"Editing image with {model_id}...")

    if not os.path.exists(input_image_path):
        logger.error(f"Input image not found: {input_image_path}")
        return None

    with open(input_image_path, "rb") as f:
        img_bytes = f.read()
    mime = "image/png" if input_image_path.endswith(".png") else "image/jpeg"

    contents = [
        prompt,
        types.Part.from_bytes(data=img_bytes, mime_type=mime)
    ]

    config = types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
        image_config=types.ImageConfig(aspect_ratio=aspect_ratio)
    )

    try:
        def _run_edit():
            return client.models.generate_content(
                model=model_id,
                contents=contents,
                config=config
            )

        response = await asyncio.to_thread(_run_edit)

        saved_path = None
        for part in response.parts:
            if part.inline_data:
                if hasattr(part, 'as_image'):
                    img = part.as_image()
                    img.save(output_file)
                    saved_path = output_file
                    logger.info(f"Edited image saved to {output_file}")

        return saved_path

    except Exception as e:
        logger.error(f"Error editing image: {e}")
        return None


async def generate_video_veo(
    prompt: str,
    output_file: str,
    duration_seconds: int = 6,
    model_alias: str = "veo_3_1"
):
    """
    Generates video using Veo 3.1.
    """
    # Placeholder - Veo API still in preview/whitelist
    logger.warning("Veo generation not yet fully implemented via public SDK.")
    return None
