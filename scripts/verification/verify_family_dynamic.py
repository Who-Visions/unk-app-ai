import sys
import os
import asyncio
import json

# Ensure we can import from the root (Robust)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from services.llm.unk_agent import UnkAiAgent

async def test_family_dynamic():
    print("--- 1. Testing UNK Mode (The Robust Uncle) ---")
    unk = UnkAiAgent(mode="unk")
    
    # Test Unk React
    res_unk = await unk.speak("Nephew, I saw you crashing out on TikTok with those masks on. What's the motion?")
    print(f"UNK Response: {res_unk}\n")

    # Test Unk Slang Friction
    res_slang = await unk.speak("Unk, what do you think of this 'Type Shit' trend?")
    print(f"UNK Slang Test: {res_slang}\n")

    print("--- 2. Testing YN Mode (The Digital Skeptic) ---")
    unk.switch_mode("yn")
    res_yn = await unk.speak("Unk keeps saying I'm cooked. He doesn't get the alignment.")
    print(f"YN Response: {res_yn}\n")

    print("--- 3. Testing AUNTIE Mode (The Wisdom Keeper) ---")
    unk.switch_mode("auntie")
    res_auntie = await unk.speak("These kids are outside acting skantless again. Should I call their momma?")
    print(f"AUNTIE Response: {res_auntie}\n")

    print("--- 4. Testing Trend Summary (Multimodal/JSON) ---")
    trend = {
        "name": "The Skibidi Fridge Challenge",
        "description": "Kids are putting fridges in their toilets.",
        "platform": "TikTok"
    }
    unk.switch_mode("unk")
    summary = await unk.summarise_trend(trend)
    print(f"UNK Trend Verdict:\n{json.dumps(summary, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_family_dynamic())
