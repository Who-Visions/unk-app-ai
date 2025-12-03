"""
Unk Dictionary Generator
========================
Uses the Unk Agent (Unk Mode) to expand the slang dictionary.
"""

import asyncio
import json
import os
from typing import List, Dict
from gemini_agent import UnkAgent
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# Define structured output for the generator
class SlangEntry(BaseModel):
    term: str = Field(..., description="The modern slang term (Yn language)")
    definition: str = Field(..., description="Standard definition")
    unk_translation: str = Field(..., description="The 'Unk' (older generation) equivalent or explanation")
    example_usage: str = Field(..., description="A sentence using the term")
    category: str = Field(..., description="Category (e.g., business, social, emotion)")
    target_audience_relevance: str = Field(..., description="High/Medium/Low relevance for 35+ professional")

class SlangBatch(BaseModel):
    entries: List[SlangEntry]

async def generate_dictionary(
    base_terms: List[str], 
    project_id: str = "unk-app-480102"
):
    agent = UnkAgent(
        mode="unk_mode",  # Use Unk Mode for the wisdom
        gcp_project=project_id,
        enable_structured_output=True
    )
    
    prompt = f"""
    We are building a "Yn to Unk" dictionary for professionals aged 35+.
    
    I need you to generate detailed dictionary entries for the following terms, 
    plus add 5 more relevant modern slang terms that you think are crucial for this audience.
    
    Focus on "Unk Translations" that use older idioms (e.g., "brown-nosing", "putting your nose to the grindstone").
    
    Base Terms: {', '.join(base_terms)}
    
    Output a JSON list of objects.
    """
    
    print(f"Generating dictionary entries using {agent.model_id}...")
    
    # We use the client directly to force the specific schema response if the agent wrapper is tricky
    # But the agent wrapper supports structured output via the wrapper.
    # Let's try the wrapper's classify/execute flow or just direct generation config.
    
    try:
        await agent.start_session()
        response = await agent.chat_session.send_message(
            prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SlangBatch
            )
        )
        
        if response.parsed:
            return response.parsed.entries
        else:
            print("Failed to parse structured output.")
            return []
            
    except Exception as e:
        print(f"Error generating dictionary: {e}")
        return []

async def main():
    # Load seed data to get started or just define a list
    seed_file = "unk_dictionary_seed.json"
    existing_data = []
    
    if os.path.exists(seed_file):
        with open(seed_file, "r") as f:
            existing_data = json.load(f)
            print(f"Loaded {len(existing_data)} existing entries.")
    
    # List of terms to expand or re-generate (just a few for testing)
    terms_to_process = ["aura", "skibidi", "sigma", "mewing", "fanum tax", "crash out"]
    
    new_entries = await generate_dictionary(terms_to_process)
    
    if new_entries:
        # Convert Pydantic models to dicts
        new_data_dicts = [entry.model_dump() for entry in new_entries]
        
        # Merge (simple de-duplication by term)
        existing_terms = {item['term'].lower() for item in existing_data}
        
        for entry in new_data_dicts:
            if entry['term'].lower() not in existing_terms:
                existing_data.append(entry)
                print(f"Added new term: {entry['term']}")
        
        # Save back to file
        with open(seed_file, "w") as f:
            json.dump(existing_data, f, indent=4)
        
        print(f"Dictionary updated. Total entries: {len(existing_data)}")
    else:
        print("No new entries generated.")

if __name__ == "__main__":
    asyncio.run(main())
