import os
from typing import Optional

from skills.chirp import generate_chirp_audio


class UnkVoiceService:
    """
    Expressive TTS service for the Unk family dynamic using Google Cloud Chirp 3 HD.
    Replaces deprecated Chatterbox implementation.
    """

    def __init__(self, device: str = "cpu"):
        # No local model loading needed for Chirp
        self.provider = "Google Chirp 3 HD"
        print(f"[UnkVoiceService] Initialized (Provider: {self.provider})")

    PERSONA_MAP = {
        "unk": "Sadachbia",   # Deep Male
        "uncle": "Sadachbia",
        "auntie": "Gacrux",  # Auntie
        "yn": "Puck",      # Young Male? Or Fenrir? Puck is Male.
        "default": "Sadachbia"
    }

    def get_voice_for_persona(self, persona: str) -> str:
        """Get the Chirp voice name for a given persona."""
        return self.PERSONA_MAP.get(persona.lower(), "Sadachbia")

    def generate_voice(
        self,
        text: str,
        ref_audio_path: str = None,
        output_path: str = "output_voice.wav",
        mood: str = "neutral",
        persona: str = "unk"
    ) -> Optional[str]:
        """
        Generates audio using Chirp 3 HD.
        Maps persona to specific Voice IDs.
        """
        voice_name = self.get_voice_for_persona(persona)

        # Determine encoding from extension
        encoding = "LINEAR16" if output_path.lower().endswith(".wav") else "MP3"

        # SSML processing for mood could happen here (e.g. adding pauses)
        # For now, we pass text directly.
        # Ideally strip [chuckle] tags if Chirp doesn't support them via SSML mapping.
        # Chirp supports standard SSML. [chuckle] is not standard.
        # We should clean text of paralinguistic tags for Chirp or map them to <break> or specific custom pronunciations.
        # Simply stripping them is safer for now.

        # Aggressive Cleaning for TTS (No "Asterisk" or "Bracket")
        import re
        # Remove asterisks (Markdown bold/italic)
        clean_text = re.sub(r'\*+', '', text)
        # Remove [Tokens] like [sigh]
        clean_text = re.sub(r'\[.*?\]', '', clean_text)
        # Remove (Parentheticals) if they look like actions? No, keep usually.
        # Just clean extra whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        try:
            # print(f"[UnkVoiceService] Synthesizing '{clean_text[:30]}...' (Voice: {voice_name})")
            return generate_chirp_audio(
                text=clean_text,
                output_file=output_path,
                voice_name=voice_name,
                encoding_format=encoding
            )
        except Exception as e:
            # print(f"[UnkVoiceService] Generation error: {e}")
            return None

    def get_ref_clip(self, persona: str) -> str:
        """Legacy helper, not needed for Chirp but kept for API compatibility."""
        return ""
