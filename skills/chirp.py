"""
Chirp 3 TTS Skill
=================
Generates high-quality speech using Google Cloud TTS Chirp 3 HD models.
Supports basic text and SSML (Speech Synthesis Markup Language).
"""
import os
from typing import Optional

from google.cloud import texttospeech

from routers.config import logger

# Common Chirp 3 HD Voices (subset)
# Format: en-US-Chirp3-HD-<Name>
CHIRP_VOICES = {
    "Charon": "en-US-Chirp3-HD-Charon",
    "Puck": "en-US-Chirp3-HD-Puck",
    "Kore": "en-US-Chirp3-HD-Kore",
    "Fenrir": "en-US-Chirp3-HD-Fenrir",
    "Aoede": "en-US-Chirp3-HD-Aoede",
    "Leda": "en-US-Chirp3-HD-Leda",
    "Zephyr": "en-US-Chirp3-HD-Zephyr",
    "Orus": "en-US-Chirp3-HD-Orus",
}


def generate_chirp_audio(
    text: str,  # Or SSML string
    output_file: str,
    voice_name: str = "Charon",  # Can be short name or full ID
    language_code: str = "en-US",
    speaking_rate: float = 1.0,
    is_ssml: bool = False,
    encoding_format: str = "MP3"  # MP3, LINEAR16, OGG_OPUS
) -> Optional[str]:
    """
    Synthesizes speech using Google Cloud TTS Chirp 3 HD.
    """
    try:
        client = texttospeech.TextToSpeechClient()

        # Resolve voice name
        full_voice_name = CHIRP_VOICES.get(voice_name, voice_name)
        if "Chirp3-HD" not in full_voice_name:
            # Default fallback if unknown simple name
            full_voice_name = f"en-US-Chirp3-HD-{voice_name}"

        logger.info(f"Generating Chirp audio (Voice: {full_voice_name}, SSML: {is_ssml})...")

        # Set input
        if is_ssml:
            synthesis_input = texttospeech.SynthesisInput(ssml=text)
        else:
            synthesis_input = texttospeech.SynthesisInput(text=text)

        # Set voice parameters
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=full_voice_name
        )

        # Resolve encoding
        encoding_map = {
            "MP3": texttospeech.AudioEncoding.MP3,
            "LINEAR16": texttospeech.AudioEncoding.LINEAR16,
            "OGG_OPUS": texttospeech.AudioEncoding.OGG_OPUS
        }
        audio_encoding = encoding_map.get(encoding_format, texttospeech.AudioEncoding.MP3)

        # Set audio configuration
        audio_config = texttospeech.AudioConfig(
            audio_encoding=audio_encoding,
            speaking_rate=speaking_rate
        )

        # Perform the text-to-speech request
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        # Write the response to the output file
        with open(output_file, "wb") as out:
            out.write(response.audio_content)
            logger.info(f"Audio content written to {output_file}")

        return output_file

    except Exception as e:
        logger.error(f"Chirp TTS Failed: {e}")
        return None


def validate_chirp_import():
    """Simple check to ensure module loads and client initializes."""
    try:
        client = texttospeech.TextToSpeechClient()
        return True
    except Exception as e:
        print(f"Chirp Client Init Failed: {e}")
        return False
