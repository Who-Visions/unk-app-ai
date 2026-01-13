"""
Synthesis Skills
================
Capabilities for Text-to-Speech (TTS) using Gemini 2.5 Flash TTS.
Supports Single and Multi-Speaker generation with configurable Voices and Styles.
"""
import asyncio
from typing import Dict, Optional

from google import genai
from google.genai import types

from gemini_agent.models_spec import get_model_id
from routers.config import GOOGLE_GENAI_API_KEY, logger
# Smart Router currently handles Text/Reasoning.
# TTS Routing could be added to SmartRouter in the future (e.g. Flash TTS vs Pro TTS).
from services.llm.smart_router import router

# Client instantiated lazily


# Define Voice Profiles as easy aliases
VOICE_PROFILES = {
    "Puck": "Puck", "Charon": "Charon", "Kore": "Kore", "Fenrir": "Fenrir",
    "Aoede": "Aoede", "Leda": "Leda", "Zephyr": "Zephyr", "Orus": "Orus"
}


async def text_to_speech(
    text: str,
    output_file: str,
    voice_name: str = "Puck",
    model_alias: str = "gemini_2_5_flash_tts"
) -> Optional[str]:
    """
    Generates single-speaker speech from text.

    Args:
        text (str): The text to say. Can include style prompts like "Say contentedly: ..."
        output_file (str): Path to save the .wav file.
        voice_name (str): The name of the voice to use (e.g., 'Puck', 'Kore').
        model_alias (str): Model to use.
    """
    model_id = get_model_id(model_alias)
    client = genai.Client(api_key=GOOGLE_GENAI_API_KEY)

    logger.info(f"Synthesizing speech with {model_id} (Voice: {voice_name})...")

    def _run_tts():
        response = client.models.generate_content(
            model=model_id,
            contents=[text],
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice_name
                        )
                    )
                )
            )
        )
        return response

    try:
        response = await asyncio.to_thread(_run_tts)
        return _save_audio_response(response, output_file)

    except Exception as e:  # pylint: disable=W0718
        logger.error(f"TTS error: {e}")
        return None


async def multi_speaker_tts(
    prompt: str,
    speakers: Dict[str, str],  # Maps "SpeakerName" -> "VoiceName"
    output_file: str,
    model_alias: str = "gemini_2_5_flash_tts"
) -> Optional[str]:
    """
    Generates multi-speaker speech.

    Args:
        prompt (str): The conversation script. Format:
                      Speaker1: Hello!
                      Speaker2: Hi there.
        speakers (Dict[str,str]): Mapping of speaker names in script to Voice names.
                                  e.g. {"Joe": "Kore", "Jane": "Puck"}
        output_file (str): Path to save result.
    """
    model_id = get_model_id(model_alias)
    client = genai.Client(api_key=GOOGLE_GENAI_API_KEY)

    logger.info(f"Synthesizing multi-speaker speech with {model_id}...")

    speaker_configs = []
    for speaker_name, voice_name in speakers.items():
        speaker_configs.append(
            types.SpeakerVoiceConfig(
                speaker=speaker_name,
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice_name
                    )
                )
            )
        )

    def _run_tts():
        response = client.models.generate_content(
            model=model_id,
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                        speaker_voice_configs=speaker_configs
                    )
                )
            )
        )
        return response

    try:
        response = await asyncio.to_thread(_run_tts)
        return _save_audio_response(response, output_file)
    except Exception as e:  # pylint: disable=W0718
        logger.error(f"Multi-speaker TTS error: {e}")
        return None


def _save_audio_response(response, output_file: str) -> Optional[str]:
    """Helper to extract and save audio from response."""
    try:
        # Check candidates
        if not response.candidates:
            logger.error("No candidates returned from TTS.")
            return None

        candidate = response.candidates[0]
        # Check parts
        for part in candidate.content.parts:
            # Inline data check
            if part.inline_data:
                # Mime type check if available, or just assume it's the audio
                if hasattr(part.inline_data, 'data'):
                    with open(output_file, "wb") as f:
                        f.write(part.inline_data.data)
                    logger.info(f"Audio saved to {output_file}")
                    return output_file

        logger.error("No audio data found in response parts.")
        return None
    except Exception as e:  # pylint: disable=W0718
        logger.error(f"Error saving audio: {e}")
        return None
