import ast
import asyncio
import json
import operator as op
import os
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from services.llm.smart_router import router

# 1. Safe calculator implementation
_ALLOWED_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
    ast.USub: op.neg,
}


def _eval_ast(node: ast.AST) -> float:
    # Support for Python 3.8+ Constant nodes and legacy Num nodes
    if hasattr(ast, 'Constant') and isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Num):
        return node.n
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_eval_ast(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](
            _eval_ast(node.left),
            _eval_ast(node.right),
        )
    raise ValueError("Unsupported expression")


def calculator(expression: str) -> str:
    """
    Safely evaluate a simple math expression.
    """
    try:
        tree = ast.parse(expression, mode="eval")
        value = _eval_ast(tree.body)
        return str(value)
    except Exception as e:
        return f"Error evaluating expression: {e}"


# 2. Model Registry (Strictest Gemini 3.0 Alignment)
GEMINI_MODELS: Dict[str, Dict[str, Any]] = {
    "gemini-3-flash-preview": {
        "modality": "multimodal",
        "input_limit": 1_048_576,
        "output_limit": 65_536,
        "supports_thinking": True,
        "supports_function_calling": True,
        "notes": "Balanced speed/intelligence model.",
    },
    "gemini-3-pro-preview": {
        "modality": "multimodal",
        "input_limit": 2_097_152,
        "output_limit": 65_536,
        "supports_thinking": True,
        "supports_function_calling": True,
        "notes": "State-of-the-art reasoning model.",
    },
    "gemini-3-pro-image-preview": {
        "modality": "image_generation",
        "supports_image_generation": True,
        "notes": "Specialized for 'vibe-coding' and visuals.",
    },
    "text-embedding-004": {
        "modality": "embeddings",
        "notes": "Standard for RAG/Semantic memory.",
    },
}


# Singleton cache for Vertex AI client (avoid re-initialization)
_CACHED_CLIENT = None
_CACHED_PROJECT = None


class GeminiAgent:
    """
    Advanced Gemini agent specialized for modern Agentic workflows.
    Supports: Async, Streaming, Tools, Multimodal (Video/Audio/PDF), Embeddings.
    Uses singleton pattern for client to avoid re-initialization latency.
    """

    def __init__(self, 
                 default_model: str = "gemini-3-flash-preview", 
                 use_vertex: bool = True,
                 api_key_env: str = "GOOGLE_API_KEY",
                 project: Optional[str] = None,
                 location: str = "global"):
        global _CACHED_CLIENT, _CACHED_PROJECT
        
        api_key = os.getenv(api_key_env)
        project = project or os.getenv("GOOGLE_CLOUD_PROJECT") or "unk-app-480102"
        location = location  # Enforce global endpoint for Gemini 3 as required

        if genai:
            # Senior Tech: We must avoid sharing AIO clients across different asyncio.run() loops.
            # Thus, we create a fresh client instance to ensure session ownership by the current loop.
            if use_vertex:
                self.client = genai.Client(
                    vertexai=True,
                    project=project,
                    location=location
                )
            else:
                self.client = genai.Client(api_key=api_key) if api_key else None
        else:
            self.client = None
            print("Warning: google-genai SDK not found.")

        self.default_model = default_model
        self.use_vertex = use_vertex
        self.api_key_env = api_key_env
        self.project = project
        self.location = location

        # Senior Tech: Persistent background event loop to manage all AI sessions.
        # This prevents loop-conflict deadlocks and ensures AIO sessions stay alive.
        self._loop = None
        self._thread = None
        self._start_background_loop()

    def _start_background_loop(self):
        import threading
        def run_loop(loop):
            asyncio.set_event_loop(loop)
            loop.run_forever()
        
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=run_loop, args=(self._loop,), daemon=True)
        self._thread.start()

    # --- Execution Flow (Async Native) ---

    async def async_run(
        self,
        prompt_content: Any,
        config: Optional[Dict[str, Any]] = None,
        stream: bool = False,
        tools: Optional[List[Any]] = None,
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Main asynchronous agent loop.
        Senior Tip: We recreate the client/session per async_run to ensure absolute 
        compatibility with the current asyncio loop, especially in threaded bot environments.
        """
        # Session-isolated client instance
        if self.use_vertex:
            client = genai.Client(
                vertexai=True,
                project=self.project,
                location=self.location
            )
        else:
            api_key = os.getenv(self.api_key_env)
            client = genai.Client(api_key=api_key) if api_key else None

        # 1. Routing & Heuristics
        text_hint = self._extract_text_hint(prompt_content)

        # 2. Smart Routing
        routed_model, routed_config = router.route(text_hint)

        # 3. Final Config Assembly
        final_gen_config = self._build_config(routed_config, config, tools)

        # 4. API Call (With 60s Timeout to prevent hangs)
        try:
            if stream:
                async def stream_gen():
                    async for chunk in await asyncio.wait_for(
                        client.aio.models.generate_content_stream(
                            model=routed_model,
                            contents=prompt_content,
                            config=final_gen_config
                        ),
                        timeout=60.0
                    ):
                        if chunk.text:
                            yield chunk.text
                return stream_gen()
            else:
                resp = await asyncio.wait_for(
                    client.aio.models.generate_content(
                        model=routed_model,
                        contents=prompt_content,
                        config=final_gen_config
                    ),
                    timeout=60.0
                )
                return self._extract_response(resp)
        except asyncio.TimeoutError:
            return "Error: AI request timed out after 60 seconds."
        except Exception as e:
            # Senior Tech: Capture safety filter blocks or network drops
            return f"AI Generation Error: {str(e)}"

    # --- Multimodal & File API ---

    async def upload_file(self, file_path: str, mime_type: Optional[str] = None) -> Any:
        """Uploads and waits for processing (for Video/PDF)."""
        if not self.client:
            return None

        file = await self.client.aio.files.upload(
            path=os.path.abspath(file_path),
            config=types.UploadFileConfig(mime_type=mime_type) if mime_type else None
        )

        # Poll if it's a video
        if mime_type and "video" in mime_type:
            while file.state == "PROCESSING":
                await asyncio.sleep(2)
                file = await self.client.aio.files.get(name=file.name)
            if file.state == "FAILED":
                raise RuntimeError(f"File {file_path} failed to process.")

        return file

    # --- Semantic Search & Embeddings ---

    async def embed(self, texts: Union[str, List[str]], model: str = "text-embedding-004") -> List[List[float]]:
        if not self.client:
            return []
        resp = await self.client.aio.models.embed_content(
            model=model,
            contents=texts
        )
        return [emb.values for emb in resp.embeddings]

    # --- Sync Interface (Compatibility) ---

    def run(self, prompt_content: Any, config: Optional[Dict[str, Any]] = None, tools: Optional[List[Any]] = None) -> str:
        """Synchronous wrapper that executes on the persistent background loop."""
        fut = asyncio.run_coroutine_threadsafe(
            self.async_run(prompt_content, config, tools=tools), 
            self._loop
        )
        try:
            return fut.result(timeout=70) # Slightly higher than internal 60s timeout
        except Exception as e:
            return f"Threaded Execution Error: {e}"

    # --- Helper Logic ---

    def _build_config(self, routed: Dict[str, Any], overrides: Optional[Dict[str, Any]], tools: Optional[List[Any]]) -> Any:
        # Merge logic
        cfg = routed.copy()
        if overrides:
            cfg.update(overrides)

        # Specialized Thinking Config mapping
        thinking_config = None
        if "thinking_config" in cfg and isinstance(cfg["thinking_config"], dict):
            tc = cfg["thinking_config"]
            thinking_config = types.ThinkingConfig(
                include_thoughts=tc.get("include_thoughts", False),
                thinking_level=self._map_thinking_level(tc.get("thinking_level", "medium"))
            )

        # Safety Settings mapping
        safety_settings = None
        if "safety_settings" in cfg:
            safety_settings = [
                types.SafetySetting(category=s["category"], threshold=s["threshold"])
                for s in cfg["safety_settings"]
            ]

        return types.GenerateContentConfig(
            system_instruction=cfg.get("system_instruction"),
            response_mime_type=cfg.get("response_mime_type"),
            response_schema=cfg.get("response_schema"),
            thinking_config=thinking_config,
            safety_settings=safety_settings,
            tools=tools or cfg.get("tools"),
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=False) if tools or cfg.get("tools") else None,
            response_modalities=cfg.get("response_modalities")
        )

    def _map_thinking_level(self, level: str) -> Any:
        mapping = {
            "high": types.ThinkingLevel.HIGH,
            "medium": types.ThinkingLevel.MEDIUM,
            "low": types.ThinkingLevel.LOW,
            "minimal": types.ThinkingLevel.MINIMAL
        }
        return mapping.get(level.lower(), types.ThinkingLevel.MEDIUM)

    def _extract_text_hint(self, content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            # Senior Tech: Peek into the LAST message for routing context
            for part in reversed(content):
                # Handle types.Content
                if hasattr(part, 'parts') and part.parts:
                    for sub in reversed(part.parts):
                        if hasattr(sub, 'text') and sub.text:
                            return sub.text
                # Handle raw str or Part
                if isinstance(part, str):
                    return part
                if hasattr(part, 'text') and part.text:
                    return part.text
        return ""

    def _is_math_expression(self, text: str) -> bool:
        norm = text.lower().strip()
        if norm.startswith("calc:"):
            return True
        return any(c in norm for c in '+-*/%^') and len(norm.split()) < 5

    def _extract_response(self, resp: Any) -> str:
        """
        Hardened extraction logic to handle text, parts, and safety blocks.
        """
        # 1. Standard approach (Try to access .text which might raise on safety blocks)
        try:
            if hasattr(resp, 'text') and resp.text:
                return resp.text
        except Exception: # pylint: disable=broad-exception-caught
            pass

        # 2. Part-based fallback (Safer manual extraction)
        out = []
        try:
            if hasattr(resp, 'candidates') and resp.candidates:
                cand = resp.candidates[0]
                if hasattr(cand, 'content') and cand.content.parts:
                    for part in cand.content.parts:
                        if hasattr(part, 'text') and part.text:
                            out.append(part.text)
                        elif hasattr(part, 'inline_data') and part.inline_data:
                            out.append(f"[Media: {part.inline_data.mime_type}]")
        except Exception: # pylint: disable=broad-exception-caught
            pass

        # 3. Parsed fallback (for structured output)
        if not out and hasattr(resp, 'parsed') and resp.parsed:
            return str(resp.parsed)

        # 4. Last resort: string representation or error message
        final = "\n".join(out) if out else ""
        if not final:
            # Check for safety reasons
            try:
                if hasattr(resp, 'candidates') and resp.candidates:
                    finish_reason = resp.candidates[0].finish_reason
                    if finish_reason:
                        return f"AI Blocked: {finish_reason}"
            except Exception: # pylint: disable=broad-exception-caught
                pass
            return str(resp)
        return final
