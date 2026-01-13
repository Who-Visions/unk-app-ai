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


class GeminiAgent:
    """
    Advanced Gemini agent specialized for modern Agentic workflows.
    Supports: Async, Streaming, Tools, Multimodal (Video/Audio/PDF), Embeddings.
    """

    def __init__(
        self,
        api_key_env: str = "GOOGLE_API_KEY",
        default_model: str = "gemini-3-flash-preview",
        use_vertex: bool = True
    ) -> None:
        api_key = os.getenv(api_key_env)
        project = os.getenv("GOOGLE_CLOUD_PROJECT") or "unk-app-480102"
        location = "global"  # Enforce global endpoint for Gemini 3 as required

        if genai:
            if use_vertex:
                print(
                    f"[GeminiAgent] Initializing Vertex AI in {location} mode (Project: {project})")
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
        # Tool Map for internal or native usage
        self.tools_map = {
            "calculator": calculator,
        }

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
        Args:
            prompt_content: str, List[Part], or file objects.
            config: Dict of GenerateContentConfig overrides.
            stream: Whether to use generate_content_stream.
            tools: List of callables to pass as native tools.
        """
        if not self.client:
            raise RuntimeError("Gemini client not initialized.")

        # 1. Routing & Heuristics
        text_hint = self._extract_text_hint(prompt_content)

        # Internal Tool Shortcut (Calculator)
        if self._is_math_expression(text_hint):
            res = calculator(text_hint.replace("calc:", "").strip())
            if stream:
                async def internal_stream():
                    yield res
                return internal_stream()
            return res

        # 2. Smart Routing
        routed_model, routed_config = router.route(text_hint)

        # 3. Final Config Assembly
        final_gen_config = self._build_config(routed_config, config, tools)

        # 4. API Call
        if stream:
            async def stream_gen():
                async for chunk in await self.client.aio.models.generate_content_stream(
                    model=routed_model,
                    contents=prompt_content,
                    config=final_gen_config
                ):
                    if chunk.text:
                        yield chunk.text
            return stream_gen()
        else:
            resp = await self.client.aio.models.generate_content(
                model=routed_model,
                contents=prompt_content,
                config=final_gen_config
            )
            return self._extract_response(resp)

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
        """Synchronous wrapper for async_run (blocking)."""
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # In some envs (like Jupyter), we might need another approach,
            # but for standard CLI/Services this is fine.
            return "Internal Error: Async loop already running. Use async_run."
        return loop.run_until_complete(self.async_run(prompt_content, config, stream=False, tools=tools))

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
            for part in content:
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
        # Handles text, thoughts, or image generation results
        out = []
        if hasattr(resp, 'text') and resp.text:
            out.append(resp.text)

        # Handle thinking/reasoning parts if requested
        # Note: thinking tokens are usually accessible via specific attributes in 2.5/3.0

        # Handle Image modality
        for part in resp.parts:
            if part.inline_data:
                # Meta-information about generated image
                out.append(f"[Media: {part.inline_data.mime_type}]")

        return "\n".join(out) if out else str(resp)
