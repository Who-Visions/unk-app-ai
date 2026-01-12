
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from skills.notion_skill import NotionSkill

def test_skill():
    print("🧪 Testing NotionSkill...")
    
    # Initialize
    skill = NotionSkill()
    if not skill.client:
        print("❌ Failed to initialize client (Warning expected if secret missing)")
        return

    # Test 1: Search
    print("\n🔍 Testing Search (Query: 'Studio')...")
    results = skill.search_observatory("Studio")
    print(f"Result Preview: {results[:200]}...")

    # Test 2: Project Routing (Dry run check only, we won't spam creates)
    print("\n🛤️ Testing DB Routing Logic...")
    web_db = skill._get_db_id_for_type("web dev")
    print(f"Web Type -> {web_db} (Expected: 2e6ca...fb85)")
    
    photo_db = skill._get_db_id_for_type("photo shoot")
    print(f"Photo Type -> {photo_db} (Expected: 2e6ca...72b)")

if __name__ == "__main__":
    test_skill()
