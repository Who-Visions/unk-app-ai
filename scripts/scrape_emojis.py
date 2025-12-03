"""
Emoji Scraper for Unk Agent
===========================
Scrapes the Unicode Full Emoji List to create a local JSON database.
"""

import requests
from bs4 import BeautifulSoup
import json
import os

URL = "https://unicode.org/emoji/charts/full-emoji-list.html"
OUTPUT_FILE = "unk_emoji_db.json"

def scrape_emojis():
    print(f"Fetching {URL}...")
    try:
        response = requests.get(URL, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch URL: {e}")
        return

    print("Parsing HTML (this may take a moment)...")
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # The chart is usually a big <table>
    # Rows <tr> contain <th> (headers) or <td> (data)
    # We look for <tr> where we can extract the 'chars' and 'name' class columns
    
    emojis = []
    rows = soup.find_all('tr')
    
    current_group = "Unknown"
    current_subgroup = "Unknown"
    
    print(f"Processing {len(rows)} rows...")
    
    for row in rows:
        # Check for group/subgroup headers
        th_group = row.find('th', class_='bighead')
        if th_group:
            current_group = th_group.get_text(strip=True)
            continue
            
        th_sub = row.find('th', class_='mediumhead')
        if th_sub:
            current_subgroup = th_sub.get_text(strip=True)
            continue
            
        # Data rows
        # Unicode chart classes: 'chars' (the emoji), 'name' (description)
        # Note: class names might vary, but 'chars' and 'name' are standard in older versions.
        # Sometimes 'chars' is just the rendered glyph.
        
        td_char = row.find('td', class_='chars')
        td_name = row.find('td', class_='name')
        
        if td_char and td_name:
            char = td_char.get_text(strip=True)
            name = td_name.get_text(strip=True)
            
            # Filter out garbage or empty rows
            if char and name:
                emojis.append({
                    "emoji": char,
                    "name": name,
                    "group": current_group,
                    "subgroup": current_subgroup
                })
    
    print(f"Found {len(emojis)} emojis.")
    
    # Post-processing: Add 'unk_tag' placeholder?
    # For now, just save the raw data.
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(emojis, f, indent=2, ensure_ascii=False)
        
    print(f"Saved database to {OUTPUT_FILE}")

if __name__ == "__main__":
    scrape_emojis()
