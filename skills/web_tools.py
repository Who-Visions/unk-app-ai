"""
Web Tools Skills
================
Capabilities for Google Search Grounding and Web Retrieval.
"""
import asyncio
from typing import Dict, Any

from google import genai
from google.genai import types

from gemini_agent.models_spec import get_model_id
from routers.config import GOOGLE_GENAI_API_KEY, logger

# Client instantiated lazily


async def search_grounding(
    prompt: str,
    model_alias: str = "gemini_3_flash"
) -> Dict[str, Any]:
    """
    Performs a generation with Google Search grounding enabled.
    """
    model_id = get_model_id(model_alias)
    client = genai.Client(api_key=GOOGLE_GENAI_API_KEY)


    def _run_search():
        return client.models.generate_content(
            model=model_id,
            contents=[prompt],
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                response_modalities=["TEXT"]
            )
        )

    try:
        response = await asyncio.to_thread(_run_search)

        result = {
            "text": response.text,
            "grounding_chunks": [],
            "search_entry_point": None
        }

        # Extract grounding metadata
        if response.candidates and response.candidates[0].grounding_metadata:
            gm = response.candidates[0].grounding_metadata
            result["search_entry_point"] = gm.search_entry_point.rendered_content if gm.search_entry_point else None

            if gm.grounding_chunks:
                for chunk in gm.grounding_chunks:
                    if chunk.web:
                         result["grounding_chunks"].append({
                             "uri": chunk.web.uri,
                             "title": chunk.web.title
                         })

        return result

    except Exception as e:  # pylint: disable=W0718
        logger.error(f"Search grounding error: {e}")
        return {"error": str(e)}

async def vertex_search_grounding(
    prompt: str,
    datastore_id: str,
    project_id: str = None,
    location: str = "global",
    model_alias: str = "default"
) -> Dict[str, Any]:
    """
    Performs a generation with Vertex AI Search grounding.
    """
    model_id = get_model_id(model_alias)

    # Retrieval Tool Config
    # Uses google.genai types for Vertex Search
    # Note: Requires fully qualified datastore resource name usually
    # projects/{project}/locations/{location}/collections/default_collection/dataStores/{datastore_id}

    # We construct the tool
    # Check SDK for exact helper, assuming standard retrieval config

    logger.info(f"Vertex Search Grounding with {datastore_id}...")

    # This is a placeholder for the exact SDK syntax for Vertex Grounding
    # which often involves:
    # tools=[types.Tool(retrieval=types.Retrieval(vertex_ai_search=types.VertexAISearch(datastore=...)))]

    return {"error": "Vertex Search implementation pending exact SDK verification."}

import httpx

async def fetch_url_content(url: str) -> str:
    """
    Simple URL fetcher for scraping content.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True, timeout=10.0)
            return response.text
    except Exception as e:  # pylint: disable=W0718
        logger.error(f"Error fetching URL {url}: {e}")
        return f"Error: {str(e)}"
