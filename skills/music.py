"""
Music Generation Skills
=======================
Capabilities for generating and steering music using Lyria RealTime.
"""
import asyncio
import os
from typing import Any, Dict, List

from google import genai
from google.genai import types

from routers.config import GOOGLE_GENAI_API_KEY, logger

# Constants
LYRIA_MODEL_ID = "models/lyria-realtime-exp"


class LyriaClient:
    """
    Client for interacting with Lyria RealTime Music Generation.
    Uses WebSockets for bidirectional communication.
    """

    def __init__(self, api_key: str = GOOGLE_GENAI_API_KEY):
        self.client = genai.Client(api_key=api_key, http_options={'api_version': 'v1alpha'})
        self.session = None

    async def connect(self):
        """Initializes the connection session."""
        try:
            self.session = await self.client.aio.live.music.connect(model=LYRIA_MODEL_ID)
            logger.info("Connected to Lyria RealTime session.")
            return self.session
        except Exception as e:  # pylint: disable=W0718
            logger.error(f"Failed to connect to Lyria: {e}")
            raise e

    async def generate_music(
        self,
        prompts: List[Dict[str, Any]],
        duration_seconds: int = 10,
        bpm: int = 90,
        temperature: float = 1.0,
        output_file: str = "output.pcm"
    ):
        """
        Generates music based on prompts for a set duration.

        Args:
            prompts: List of dicts like {"text": "techno", "weight": 1.0}
            duration_seconds: How long to record/generate.
            bpm: Beats per minute.
            temperature: Creativity (0.0 to 3.0).
            output_file: File to save raw PCM audio.
        """
        if not self.session:
            await self.connect()

        weighted_prompts = [
            types.WeightedPrompt(text=p["text"], weight=p.get("weight", 1.0))
            for p in prompts
        ]

        async def receive_audio(session, duration, filepath):
            """Background task to receive and save audio."""
            logger.info(f"Recording music to {filepath}...")
            start_time = asyncio.get_running_loop().time()

            with open(filepath, "wb") as f:
                async for message in session.receive():
                    if message.server_content and message.server_content.audio_chunks:
                        for chunk in message.server_content.audio_chunks:
                            f.write(chunk.data)

                    if asyncio.get_running_loop().time() - start_time > duration:
                        logger.info("Duration reached. Stopping recording.")
                        break

                    await asyncio.sleep(0.001)  # Yield

        try:
            async with asyncio.TaskGroup() as tg:
                # Start receiver
                receiver_task = tg.create_task(receive_audio(
                    self.session, duration_seconds, output_file))

                # Send config
                await self.session.set_music_generation_config(
                    config=types.LiveMusicGenerationConfig(bpm=bpm, temperature=temperature)
                )

                # Send prompts
                await self.session.set_weighted_prompts(prompts=weighted_prompts)

                # Start play
                await self.session.play()

                # Wait for receiver to finish (which finishes on duration)
                # Note: This is a simplifiction; in a real app we might want independent control.
                await receiver_task

                # Stop session
                # await self.session.stop() # Optional if we are closing

        except Exception as e:  # pylint: disable=W0718
            logger.error(f"Error during music generation: {e}")
        finally:
            logger.info("Lyria session finished.")

# Example Usage Helper


async def generate_track(prompt_text: str, duration: int = 15, output_path: str = "track.pcm"):
    """Simple wrapper for one-shot generation."""
    lyria = LyriaClient()
    await lyria.generate_music(
        prompts=[{"text": prompt_text, "weight": 1.0}],
        duration_seconds=duration,
        output_file=output_path
    )
    return os.path.abspath(output_path)
