"""
DOAC Wisdom Ingestion Script
============================
Processes transcripts from The Diary Of A CEO and ingests into BigQuery vector store.
Adapted for Unk Agent.
"""
import json
import argparse
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.vector_store_bigquery import BigQueryVectorStore
from routers.config import GCP_PROJECT, GCP_LOCATION

# Constants
PROJECT_ID = GCP_PROJECT
LOCATION = GCP_LOCATION
DEFAULT_TRANSCRIPTS_DIR = PROJECT_ROOT / "data" / "transcripts"

class Colors:
    """ANSI Colors."""
    NEON_RED = "\033[91m"
    NEON_GREEN = "\033[92m"
    NEON_YELLOW = "\033[93m"
    NEON_BLUE = "\033[94m"
    NEON_CYAN = "\033[96m"
    RESET = "\033[0m"

# Guest category mapping for better retrieval
GUEST_CATEGORIES = {
    # Mindset & Psychology
    "Robert Greene": ["mindset", "power", "strategy", "manipulation", "seduction"],
    "Jordan Peterson": ["mindset", "psychology", "self-improvement", "meaning"],
    "Gabor Mate": ["psychology", "trauma", "health", "addiction"],
    "Doctor Gabor Mate": ["psychology", "trauma", "health", "addiction"],
    "Donald Hoffman": ["psychology", "perception", "consciousness", "reality"],
    
    # Health & Neuroscience
    "Dr Tara Swart": ["neuroscience", "brain", "stress", "manifestation"],
    "Dr. Tara Swart": ["neuroscience", "brain", "stress", "manifestation"],
    "Dr Joe Dispenza": ["neuroscience", "meditation", "manifestation", "mindset"],
    "Matthew Walker": ["sleep", "health", "neuroscience", "performance"],
    "Dr Daniel Amen": ["brain", "ADHD", "neuroscience", "mental-health"],
    "Doctor Tim Spector": ["nutrition", "diet", "gut-health", "weight-loss"],
    "Dr Will Bulsiewicz": ["gut-health", "nutrition", "digestion"],
    "Dr. Mindy Pelz": ["fasting", "health", "hormones", "weight-loss"],
    "Dr Rena Malik": ["health", "sexual-health", "urology"],
    "Dr Vonda Wright": ["fitness", "aging", "exercise", "longevity"],
    "Dr Michael Israetel": ["fitness", "muscle", "exercise", "bodybuilding"],
    "Dr. Pradip Jamnadas": ["metabolic-health", "insulin", "fasting"],
    "Giles Yeo": ["nutrition", "weight-loss", "calories", "diet"],
    "Gary Brecka": ["biohacking", "DNA", "health", "optimization"],
    "Jessie Inchauspé": ["glucose", "nutrition", "metabolic-health"],
    "Glucose Goddess": ["glucose", "nutrition", "metabolic-health"],
    "Doctor Jason Fung": ["fasting", "weight-loss", "insulin", "metabolic-health"],
    "Mary Claire Haver": ["menopause", "women-health", "hormones"],
    
    # AI & Technology
    "Mo Gawdat": ["AI", "technology", "future", "existential-risk"],
    "Dr. Roman Yampolskiy": ["AI-safety", "technology", "future-of-work"],
    "Eric Weinstein": ["technology", "society", "economics", "physics"],
    "Walter Isaacson": ["biography", "Elon-Musk", "innovation", "leadership"],
    "Sam Altman": ["AI", "technology", "future", "openai"],
    
    # Finance & Wealth
    "Alex Hormozi": ["business", "wealth", "entrepreneurship", "scaling"],
    "Codie Sanchez": ["business", "wealth", "entrepreneurship", "acquisitions"],
    "Morgan Housel": ["finance", "investing", "psychology-of-money"],
    "Ray Dalio": ["finance", "investing", "economics", "macro"],
    "Raoul Pal": ["crypto", "investing", "macro-economics"],
    "Ramit Sethi": ["personal-finance", "wealth", "money-mindset"],
    "Jaspreet Singh": ["personal-finance", "investing", "wealth"],
    "Kevin O'Leary": ["business", "investing", "entrepreneurship"],
    "Mohnish Pabrai": ["investing", "value-investing", "wealth"],
    "Dame Dash": ["business", "entrepreneurship", "hip-hop", "ownership"],
    
    # Communication & Influence
    "Andrew Bustamante": ["CIA", "intelligence", "deception", "strategy"],
    "Evy Poumpouras": ["interrogation", "body-language", "deception", "secret-service"],
    "Chase Hughes": ["behavior", "influence", "body-language", "persuasion"],
    "Body Language Expert": ["body-language", "communication", "influence"],
    "Speaking Coach": ["communication", "public-speaking", "confidence"],
    
    # Relationships & Life
    "James J Sexton": ["relationships", "divorce", "marriage", "legal"],
    "Simon Sinek": ["leadership", "purpose", "motivation", "business"],
    "Scott Galloway": ["business", "society", "generational", "economics"],
    "Trevor Noah": ["entertainment", "mental-health", "ADHD", "comedy"],
    "Jimmy Carr": ["comedy", "men", "society", "entertainment"],
    "Cole Sprouse": ["entertainment", "childhood", "fame", "mental-health"],
    "Simon Cowell": ["entertainment", "music-industry", "success", "loss"],
    "James Hoffmann": ["coffee", "mental-health", "expertise"]
}


def categorize_guest(guest: str) -> List[str]:
    """Get categories for a guest, with fallback."""
    if guest in GUEST_CATEGORIES:
        return GUEST_CATEGORIES[guest]
    
    # Try partial matching
    for known_guest, categories in GUEST_CATEGORIES.items():
        if known_guest.lower() in guest.lower() or guest.lower() in known_guest.lower():
            return categories
    
    return ["general", "wisdom"]


def format_chunk_for_ingestion(
    chunk: Dict, 
    video_title: str, 
    guest: str, 
    video_id: str,
    chunk_index: int
) -> Dict:
    """Format a transcript chunk for BigQuery ingestion."""
    categories = categorize_guest(guest)
    
    # Create rich content with context
    start_fmt = f"{int(chunk['start_time']//60)}:{int(chunk['start_time']%60):02d}"
    end_fmt = f"{int(chunk['end_time']//60)}:{int(chunk['end_time']%60):02d}"
    
    text = chunk.get('text', '').strip()
    
    content = f"""Source: The Diary Of A CEO
Guest: {guest}
Episode: {video_title}
Timestamp: {start_fmt} - {end_fmt}
Categories: {', '.join(categories)}

{text}"""
    
    metadata = {
        "source": "DOAC",
        "guest": guest,
        "video_id": video_id,
        "video_title": video_title,
        "chunk_index": chunk_index,
        "start_time": chunk.get('start_time'),
        "end_time": chunk.get('end_time'),
        "categories": categories
    }
    
    return {
        "content": content,
        "metadata": metadata
    }


def ingest_transcripts(
    transcripts_dir: Path,
    dry_run: bool = False,
    limit: Optional[int] = None
) -> Dict:
    """
    Ingest all transcript chunks into BigQuery.
    """
    results = {
        "videos_processed": 0,
        "chunks_ingested": 0,
        "errors": []
    }
    
    if not transcripts_dir.exists():
        print(f"{Colors.NEON_RED}❌ Transcripts directory not found: {transcripts_dir}{Colors.RESET}")
        return results
    
    transcript_files = list(transcripts_dir.glob("*.json"))
    
    if not transcript_files:
        print(f"{Colors.NEON_YELLOW}⚠️ No transcripts found in {transcripts_dir}{Colors.RESET}")
        return results
    
    if limit:
        transcript_files = transcript_files[:limit]
    
    print(f"\n{Colors.NEON_CYAN}🧠 DOAC Wisdom Ingestion for Unk Agent{Colors.RESET}")
    print("=" * 60)
    print(f"📁 Found {len(transcript_files)} transcript files in {transcripts_dir}")
    
    store = None
    if dry_run:
        print(f"{Colors.NEON_YELLOW}🔍 DRY RUN MODE - No data will be written{Colors.RESET}")
    else:
        # Initialize BigQuery store
        bq_location = "US" if LOCATION == "global" else LOCATION
        store = BigQueryVectorStore(PROJECT_ID, bq_location)
        store.initialize_dataset()
        
    existing_ids = set()
    if store and not dry_run:
        print("🔍 Checking for existing videos in BigQuery to resume...")
        existing_ids = store.get_existing_video_ids()
        print(f"   Found {len(existing_ids)} already processed videos.")
    
    for i, transcript_file in enumerate(transcript_files, 1):
        try:
            with open(transcript_file, 'r', encoding='utf-8') as f:
                transcript = json.load(f)
            
            video_id = transcript.get('video_id', transcript_file.stem)
            
            if video_id in existing_ids:
                print(f"[{i}/{len(transcript_files)}] ⏭️  Skipping {video_id} (Already Ingested)")
                continue
            title = transcript.get('title', 'Unknown')[:60]
            guest = transcript.get('guest', 'Unknown')
            chunks = transcript.get('chunks', [])
            
            print(f"\n[{i}/{len(transcript_files)}] 📥 {title}")
            print(f"   Guest: {guest} | Chunks: {len(chunks)}")
            
            for j, chunk in enumerate(chunks):
                formatted = format_chunk_for_ingestion(
                    chunk=chunk,
                    video_title=transcript.get('title', ''),
                    guest=guest,
                    video_id=video_id,
                    chunk_index=j
                )
                
                if not dry_run and store:
                    store.add_memory(formatted['content'], formatted['metadata'])
                
                results["chunks_ingested"] += 1
            
            results["videos_processed"] += 1
            
        except Exception as e:
            print(f"   {Colors.NEON_RED}❌ Error: {e}{Colors.RESET}")
            results["errors"].append({"file": str(transcript_file), "error": str(e)})
    
    # Summary
    print("\n" + "=" * 60)
    print(f"{Colors.NEON_GREEN}✅ Ingestion Complete!{Colors.RESET}")
    print(f"   Videos: {results['videos_processed']}")
    print(f"   Chunks: {results['chunks_ingested']}")
    print(f"   Errors: {len(results['errors'])}")
    
    if dry_run:
        print(f"\n{Colors.NEON_YELLOW}This was a dry run. Use --ingest to actually push to BigQuery.{Colors.RESET}")
    
    return results


def search_wisdom(query: str, top_k: int = 5):
    """Test search against ingested DOAC wisdom."""
    bq_location = "US" if LOCATION == "global" else LOCATION
    store = BigQueryVectorStore(PROJECT_ID, bq_location)
    
    print(f"\n🔍 Searching DOAC wisdom for: '{query}'")
    print("=" * 60)
    
    results = store.search_similar(query, limit=top_k)
    
    if not results:
        print("No results found.")
        return
    
    for i, result in enumerate(results, 1):
        content = result.get('content', '')[:300]
        metadata = result.get('metadata', {})
        similarity = result.get('similarity', 0)
        
        # Parse metadata if it's a string (BigQuery might return it as dict if struct, but code says JSON str in add_memory)
        # BigQuery Python client returns dict for JSON columns usually.
        # But vector_store_bigquery.py stores it as json.dumps string?
        # Let's check vector_store_bigquery.py: 
        #   "metadata": json.dumps(metadata) if metadata else None
        # And search_similar says:
        #   "metadata": row.metadata
        # If the schema is JSON, row.metadata is likely a dict.
        
        guest = "Unknown"
        if isinstance(metadata, dict):
            guest = metadata.get('guest', 'Unknown')
        elif isinstance(metadata, str):
            try:
                m_dict = json.loads(metadata)
                guest = m_dict.get('guest', 'Unknown')
            except:
                pass
        
        print(f"\n[{i}] Similarity: {similarity:.3f}")
        print(f"    Guest: {guest}")
        print(f"    {content}...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DOAC Wisdom Ingestion for Unk Agent")
    parser.add_argument('--dry-run', action='store_true', help="Preview without writing to BigQuery")
    parser.add_argument('--ingest', action='store_true', help="Actually ingest to BigQuery")
    parser.add_argument('--limit', type=int, help="Limit number of videos to process")
    parser.add_argument('--search', type=str, help="Test search query against ingested wisdom")
    parser.add_argument('--source', type=str, help="Custom transcripts directory")
    
    args = parser.parse_args()
    
    if args.search:
        search_wisdom(args.search)
    elif args.ingest or args.dry_run:
        source_dir = Path(args.source) if args.source else DEFAULT_TRANSCRIPTS_DIR
        ingest_transcripts(
            transcripts_dir=source_dir,
            dry_run=args.dry_run,
            limit=args.limit
        )
    else:
        print("DOAC Wisdom Ingestion for Unk Agent")
        print("=" * 40)
        print("Usage:")
        print("  --dry-run    Preview ingestion without writing")
        print("  --ingest     Actually write to BigQuery")
        print("  --limit N    Process only N videos")
        print("  --search Q   Search ingested wisdom")
        print(f"  --source D   Custom transcripts dir (Default: {DEFAULT_TRANSCRIPTS_DIR})")

Unk = Uncle
Target: 35+ users
