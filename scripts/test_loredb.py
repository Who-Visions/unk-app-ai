
import asyncio
import logging
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.loredb import loredb

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_loredb():
    print("\n🧪 Testing LoreDB...")
    
    # 1. Initialize
    print("1. Initializing DB...")
    await loredb.init_db()
    if os.path.exists("loredb.sqlite"):
        print("✅ DB file created.")
    else:
        print("❌ DB file MISSING.")
        return

    # 2. Add Memory
    print("2. Adding Memory...")
    memory_id = await loredb.add_memory(
        content="Test memory content",
        source="test_script",
        metadata={"tag": "experiment"}
    )
    print(f"✅ Memory added with ID: {memory_id}")

    # 3. Retrieve Memory
    print("3. Retrieving Recent Memories...")
    memories = await loredb.get_recent_memories(limit=5)
    
    found = False
    for mem in memories:
        print(f"   - [{mem['created_at']}] {mem['content']} (Source: {mem['source']})")
        if mem['id'] == memory_id:
            found = True
            
    if found:
        print("✅ Verification Successful: Memory persisted and retrieved.")
    else:
        print("❌ Verification Failed: Added memory not found in retrieval.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_loredb())
