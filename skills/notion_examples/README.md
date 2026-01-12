# Notion Examples Cookbook
This directory contains reference implementations of official [Notion API Examples](https://developers.notion.com/page/examples), adapted for the `NotionSkill` class.

## 📂 Structure
- `basic/`: Introductory block and text operations.
- `intermediate/`: Database querying and web integrations.
- `advanced/`: Complex sync logic patterns.

## 🚀 Examples Implemented

### Introductory
1.  **Create Blocks** (`basic/1_create_blocks.py`)
    - Demonstrates creating headings, paragraphs, and to-do lists.
2.  **Linked Blocks** (`basic/2_linked_blocks.py`)
    - Shows how to mention users and link to databases inline.
3.  **Parse Text** (`basic/3_parse_text.py`)
    - Recursive logic to extract plain text from any block structure.

### Intermediate
1.  **Query Database** (`intermediate/1_query_db.py`)
    - Filtering and sorting database queries via `notion.query_database`.
2.  **Web Form Handler** (`intermediate/2_web_form_handler.py`)
    - Simulates processing a JSON payload (e.g., from Typeform or a React app) and creating a structured lead in Notion.

### Advanced
1.  **Spotify Sync** (`advanced/1_spotify_sync.py`)
    - Logic for syncing external metadata (Tracks) into Notion pages with Embed blocks.
2.  **GitHub Sync** (`advanced/2_github_sync.py`)
    - Logic for "Upserting" (Update if exists, Create if new) external resources like Issues into a Project Tracker.

## 🛠️ Usage
Run any script directly using the project python:
```bash
python skills/notion_examples/basic/1_create_blocks.py
python skills/notion_examples/advanced/2_github_sync.py
```

## 📝 Setup
Ensure your `.env` contains:
- `NOTION_WHO_VISIONS_SECRET` (or `NOTION_OBSERVATORY_SECRET`)
- `GOOGLE_CLOUD_PROJECT` (for general context)

All scripts utilize `skills.notion_skill.NotionSkill` for authentication and API wrapping.
