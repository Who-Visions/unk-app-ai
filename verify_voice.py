import asyncio
import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())

from services.audio.voice_service import UnkVoiceService

def test_voice_gen():
    print("--- Testing UnkVoiceService with Sam Jackson Reference ---")
    service = UnkVoiceService(device="cpu") # Force CPU for verification stability
    
    if not service.model:
        print("❌ Model not loaded. Check Chatterbox installation.")
        return

    ref_clip = "assets/clips/jackson_bas_sgtwest.mp3"
    text = "Nephew, I told you about those Global Endpoints. Why you still looping in central? [chuckle] Get it together."
    output = "assets/clips/unk_sam_test.wav"
    
    print(f"Generating voice using: {ref_clip}")
    result = service.generate_voice(text, ref_clip, output_path=output, mood="amused")
    
    if result:
        print(f"✅ Voice generated successfully: {result}")
    else:
        print("❌ Voice generation failed.")

if __name__ == "__main__":
    test_voice_gen()
