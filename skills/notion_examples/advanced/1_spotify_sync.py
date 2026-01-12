
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
load_dotenv()

from skills.notion_skill import NotionSkill

MOCK_SPOTIFY_TRACKS = [
    {"name": "Bohemian Rhapsody", "artist": "Queen", "album": "A Night at the Opera", "url": "https://spotify.com/track/1"},
    {"name": "Imagine", "artist": "John Lennon", "album": "Imagine", "url": "https://spotify.com/track/2"}
]

def example_spotify_sync():
    """
    Simulates syncing Spotify playlist to Notion Content Library.
    """
    notion = NotionSkill()
    # DB: Content Library
    db_id = "d23d02a7bec54167b6179111c5a48e05"

    print("🎵 Starting Spotify Sync...")

    for track in MOCK_SPOTIFY_TRACKS:
        print(f"Syncing: {track['name']} - {track['artist']}")

        # 1. Create Page
        res = notion.create_page(
            parent_id=db_id,
            title=track["name"],
            properties={
                "Type": {"select": {"name": "Audio"}}, # Assuming Type property exists
                "Status": {"select": {"name": "To Listen"}}
            },
            children=[
                {
                    "object": "block",
                    "type": "embed",
                    "embed": {"url": track["url"]}
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"text": {"content": f"Artist: {track['artist']}\nAlbum: {track['album']}"}}
                        ]
                    }
                }
            ]
        )
        if "id" in res:
            print(f"  -> Added {track['name']}")
        else:
            print(f"  -> Failed: {res.get('error')}")

if __name__ == "__main__":
    example_spotify_sync()
