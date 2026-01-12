"""
Audio Skills
============
Capabilities for Audio Input, Analysis, and Transcription using Gemini.
Supports uploading audio files via the Files API or passing inline data.
"""
import asyncio
import mimetypes


from google.genai import types

from gemini_agent.models_spec import get_model_id
from routers.config import logger

# Client instantiated lazily


async def describe_audio(
    audio_path: str,
    prompt: str = "Describe this audio clip.",
    model_alias: str = "gemini_2_5_flash"
) -> str:
    """
    Analyzes an audio file and returns a description or answer based on the prompt.
    Uses Files API for larger files/reusability.
    """
    model_id = get_model_id(model_alias)
    logger.info(f"Analyzing audio {audio_path} with {model_id}...")

    def _run_analysis():
        # Upload file
        # Note: In a real agent, we might cache these uploads or check if already uploaded
        # For this skill, we upload fresh for simplicity, but consider cleanup in production.

        # Determine mime type
        mime_type, _ = mimetypes.guess_type(audio_path)
        if not mime_type:
             mime_type = "audio/mp3" # Fallback

        logger.info(f"Uploading {audio_path} ({mime_type})...")
        uploaded_file = client.files.upload(
            file=audio_path,
            config=types.UploadFileConfig(mime_type=mime_type)
        )

        # Wait for processing if necessary (Video usually needs it, Audio is fast)
        # client.files.get(name=uploaded_file.name) # Check state if needed

        response = client.models.generate_content(
            model=model_id,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_uri(
                            file_uri=uploaded_file.uri,
                            mime_type=uploaded_file.mime_type
                        ),
                        types.Part.from_text(text=prompt)
                    ]
                )
            ]
        )
        return response.text

    try:
        response_text = await asyncio.to_thread(_run_analysis)
        return response_text
    except Exception as e:  # pylint: disable=W0718
        logger.error(f"Audio analysis error: {e}")
        return f"Error processing audio: {e}"

async def transcribe_audio(
    audio_path: str,
    timestamps: bool = True,
    model_alias: str = "gemini_2_5_flash"
) -> str:
    """
    Generates a transcript for the audio file.
    """
    prompt = "Generate a transcript of the speech."
    if timestamps:
        prompt += " Include timestamps."

    return await describe_audio(audio_path, prompt, model_alias)

async def count_audio_tokens(audio_path: str, model_alias: str = "gemini_2_5_flash") -> int:
    """
    Counts tokens for an audio file.
    """
    model_id = get_model_id(model_alias)

    def _run_count():
        mime_type, _ = mimetypes.guess_type(audio_path)
        if not mime_type: mime_type = "audio/mp3"

        uploaded_file = client.files.upload(
            file=audio_path,
            config=types.UploadFileConfig(mime_type=mime_type)
        )

        response = client.models.count_tokens(
            model=model_id,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_uri(
                            file_uri=uploaded_file.uri,
                            mime_type=uploaded_file.mime_type
                        )
                    ]
                )
            ]
        )
        return response.total_tokens

    try:
        return await asyncio.to_thread(_run_count)
    except Exception as e:  # pylint: disable=W0718
        logger.error(f"Token count error: {e}")
        return -1
