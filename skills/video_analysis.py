"""
Video Analysis Skill
====================
Provides capabilities to analyze video content using Gemini's File API and Multimodal capabilities.
Leverages the centralized GeminiAgent and SmartRouter for execution.
"""
import asyncio
import os
import time
from typing import Any, Dict, List

from google import genai
from google.genai import types

from routers.config import GOOGLE_GENAI_API_KEY, logger
from services.llm.gemini_agent import GeminiAgent

# Initialize Agent (which uses Smart Router)
agent = GeminiAgent()


def upload_video_from_path(video_path: str, poll_interval: int = 5) -> Any:
    """
    Uploads a video to the File API and waits for it to be processed.

    Args:
        video_path: Absolute path to the video file.
        poll_interval: Seconds to wait between status checks.

    Returns:
        The uploaded file object (types.File) or raises Exception.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Use raw client for file operations (Agent doesn't wrap File API yet)
    # We can reuse the agent's client if available
    client = agent.client
    if not client:
        # Fallback init
        client = genai.Client(api_key=GOOGLE_GENAI_API_KEY)

    logger.info(f"Uploading video: {video_path}...")

    # 1. Upload
    try:
        video_file = client.files.upload(file=video_path)
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise

    logger.info(f"Upload complete. File URI: {video_file.uri}. Waiting for processing...")

    # 2. Poll for Active State
    while video_file.state.name == "PROCESSING":
        time.sleep(poll_interval)
        video_file = client.files.get(name=video_file.name)
        logger.debug(f"Video state: {video_file.state.name}")

    if video_file.state.name == "FAILED":
        raise ValueError(f"Video processing failed: {video_file.state.name}")

    logger.info(f"Video is ACTIVE and ready for analysis.")
    return video_file


async def analyze_video(
    video_input: str,
    prompt: str = "Describe this video in detail.",
    is_url: bool = False
) -> str:
    """
    Analyzes a video (local path or valid File URI/YouTube URL).

    Args:
        video_input: Path to local file OR a YouTube URL.
        prompt: The question or instruction for analysis.
        is_url: Set to True if video_input is a YouTube URL.

    Returns:
        Analysis text.
    """
    try:
        content_part = None

        if is_url:
            # YouTube or direct URI support
            # Note: For YouTube, the SDK usually handles it via Part.from_uri or text prompt with link?
            # The cookbook suggests Part.from_uri for YouTube?
            # Actually, standard File API doesn't ingest YouTube directly unless downloaded.
            # But Gemini 1.5+ supports youtube URLs in some contexts.
            # Best practice: "Part.from_uri(file_uri=..., mime_type='video/*')"
            content_part = types.Part.from_uri(file_uri=video_input, mime_type="video/mp4")
        else:
            # Local File
            # 1. Upload & Process
            # Blocking call in async wrapper - ideally run in executor if heavy
            # For now, we'll run it directly as simple blockage
            video_file = await asyncio.to_thread(upload_video_from_path, video_input)

            # 2. Create Content Part
            # The SDK might allow passing the file object directly or its URI
            content_part = video_file

        # 3. Construct Multimodal Prompt
        # [VideoPart, TextPrompt]
        multimodal_prompt = [content_part, prompt]

        # 4. Generate via Agent (Smart Router will see the text prompt)
        logger.info(f"Sending video analysis request to Agent...")

        # Agent.run expects prompt_content. It will allow SmartRouter to see 'prompt' string.
        # SmartRouter likely routes to Pro for "describe", "analyze".
        response = await asyncio.to_thread(agent.run, multimodal_prompt)

        return response

    except Exception as e:
        logger.error(f"Video analysis error: {e}")
        return f"Error analyzing video: {e}"
