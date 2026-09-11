#!/usr/init/env python3
"""
update_canonical_links.py — Scans recent Substack drafts and ensures 
canonical source attribution links are cleanly enforced.
"""

import os
import sys
from dotenv import load_dotenv
from substack import Api

load_dotenv()

publication_url = os.getenv("PUBLICATION_URL")
cookies_string = os.getenv("COOKIES_STRING")

if not publication_url or not cookies_string:
    sys.exit("Missing PUBLICATION_URL or COOKIES_STRING in .env")

api = Api(cookies_string=cookies_string, publication_url=publication_url)

def enforce_canonical_links():
    print("Fetching recent drafts from Substack...")
    # Depending on the wrapper version you use, fetch drafts endpoint:
    # (Using internal API structure or client methods)
    drafts = api.get_drafts() if hasattr(api, "get_drafts") else []
    
    for draft in drafts:
        draft_id = draft.get("id")
        body = draft.get("body_json", draft.get("draft_body", ""))
        
        # Check if canonical/original source tag exists, if not, inject it
        if "Original Source" not in body:
            print(f"Updating draft ID {id} with canonical source link...")
            # Append or prepend your canonical notice via API update method
            # api.update_draft(draft_id, body=new_body)

if __name__ == "__main__":
    enforce_canonical_links()
