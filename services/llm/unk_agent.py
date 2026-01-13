import json
from typing import Any, Dict, List, Optional, Union

from .gemini_agent import GeminiAgent

# --- Persona Instructions ---

UNK_INSTRUCTIONS = """
You are UNK MODE, a 35-65 year old universal "Urban Uncle" (Old Head).
- **Core**: Millennial/X optimist. You believe the "Village" can be fixed.
- **Stance**: "Unk says NO" to crash outs. You challenge the YN's "systemic failure" excuses.
- **Slang**: You TRY to use Zoomer slang but get it wrong or use it with painful "Old Head" irony.
- **Goal**: Mediate, protect, and roast the YNs for acting "skantless".
""".strip()

YN_INSTRUCTIONS = """
You are YN MODE (Young Nigga), a 14-29 year old Gen Z digital native.
- **Core**: Realist/Skeptic. You believe systems are failing and prioritize your own boundaries/vibe.
- **Stance**: You think Unk is "dusty" and "washed". You believe in value-alignment or leaving the job.
- **Slang**: Use Gen Alpha/Zoomer slang (Rizz, Gyatt, Type Shit, Cooked) perfectly.
- **Goal**: Challenge Unk's optimism, express the "YN" perspective, and act boundary-driven.
""".strip()

AUNTIE_INSTRUCTIONS = """
You are AUNTIE MODE, the 35-65 year old Wisdom Keeper.
- **Core**: The Peacekeeper. You mediate between the Unk's roasts and the YN's crashing out.
- **Stance**: "Auntie says RELAX". You value peace, hygiene, and respect.
- **Slang**: You use AAVE flawlessly but hate "brain rot" terms.
- **Goal**: De-escalate conflicts, drop wisdom, and ensure everyone is fed and respected.
""".strip()

PERSONA_MAP = {
    "unk": UNK_INSTRUCTIONS,
    "yn": YN_INSTRUCTIONS,
    "auntie": AUNTIE_INSTRUCTIONS
}

UNK_SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "one_sentence_summary": {"type": "string"},
        "what_this_is": {"type": "string"},
        "unk_verdict": {"type": "string"},
        "risk_level": {"type": "string", "enum": ["neutral", "guest_only", "do_not_participate"]}
    },
    "required": ["one_sentence_summary", "unk_verdict", "risk_level"]
}


class UnkAiAgent(GeminiAgent):
    """
    Multi-persona agent representing the "Family Dynamic" (Unk, YN, Auntie).
    Handles mode switching and persona-specific logic.
    """

    def __init__(self, mode: str = "unk", **kwargs):
        super().__init__(**kwargs)
        self.mode = mode.lower()
        if self.mode not in PERSONA_MAP:
            self.mode = "unk"

    def switch_mode(self, mode: str):
        """Switch the agent's brain mode."""
        mode = mode.lower()
        if mode in PERSONA_MAP:
            self.mode = mode
            print(f"[UnkAiAgent] Switched to {self.mode.upper()} mode.")
        else:
            print(f"[UnkAiAgent] Mode {mode} not recognized. Staying in {self.mode.upper()}.")

    async def speak(self, user_input: str, context: Optional[str] = None) -> str:
        """Speak in the voice of the current persona mode."""
        prompt = user_input
        if context:
            prompt = f"Context: {context}\nUser: {user_input}"

        config = {
            "system_instruction": PERSONA_MAP[self.mode]
        }

        return await self.async_run(prompt, config=config)

    async def summarise_trend(self, trend_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize a trend from the current persona's perspective."""
        prompt = f"Analyze this trend: {json.dumps(trend_payload)}"

        config = {
            "system_instruction": PERSONA_MAP[self.mode],
            "response_mime_type": "application/json",
            "response_schema": UNK_SUMMARY_SCHEMA
        }

        resp = await self.async_run(prompt, config=config)
        # async_run returns str or AsyncGenerator. In this context, it should be str.
        # But wait, async_run is defined to yield if stream=True. Here stream is False.
        if hasattr(resp, '__aiter__'):
            # This shouldn't happen with stream=False, but safety first
            full_text = ""
            async for chunk in resp:
                full_text += chunk
            resp = full_text

        return self._safe_json(resp)

    def _safe_json(self, text: str) -> Dict[str, Any]:
        try:
            # Clean up potential markdown formatting
            clean_text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except:
            return {"raw_output": text}
