#!/usr/bin/env python3
"""
Convert bookmarks HTML export to captured_tabs.jsonl format.

Usage:
    python convert_bookmarks.py bookmarks.html

Appends to ~/captured_tabs.jsonl (same file the capture server uses).
"""

import sys
import json
import re
from datetime import datetime, timezone
from pathlib import Path


def extract_bookmarks(html_content: str) -> list:
    """Extract URLs and titles from bookmarks HTML."""
    # Match <A HREF="url">title</A> pattern
    pattern = r'<A\s+HREF="([^"]+)"[^>]*>([^<]+)</A>'
    matches = re.findall(pattern, html_content, re.IGNORECASE)
    
    bookmarks = []
    seen_urls = set()
    
    for url, title in matches:
        # Skip duplicates
        if url in seen_urls:
            continue
        seen_urls.add(url)
        
        # Skip non-http URLs
        if not url.startswith(('http://', 'https://')):
            continue
        
        bookmarks.append({
            "url": url,
            "title": title.strip(),
            "note": "from bookmark backlog",
            "captured_at": datetime.now(timezone.utc).isoformat()
        })
    
    return bookmarks


def main():
    if len(sys.argv) < 2:
        print("Usage: python convert_bookmarks.py <bookmarks.html>")
        sys.exit(1)
    
    input_file = Path(sys.argv[1])
    if not input_file.exists():
        print(f"File not found: {input_file}")
        sys.exit(1)
    
    output_file = Path.home() / "captured_tabs.jsonl"
    
    # Read bookmarks
    html_content = input_file.read_text(encoding="utf-8", errors="ignore")
    bookmarks = extract_bookmarks(html_content)
    
    print(f"Found {len(bookmarks)} unique bookmarks")
    
    # Check what's already captured (avoid duplicates)
    existing_urls = set()
    if output_file.exists():
        with open(output_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        existing_urls.add(json.loads(line).get("url"))
                    except:
                        pass
    
    # Filter to new only
    new_bookmarks = [b for b in bookmarks if b["url"] not in existing_urls]
    print(f"New (not already captured): {len(new_bookmarks)}")
    
    if not new_bookmarks:
        print("Nothing new to add.")
        return
    
    # Append to jsonl
    with open(output_file, "a", encoding="utf-8") as f:
        for bookmark in new_bookmarks:
            f.write(json.dumps(bookmark) + "\n")
    
    print(f"Appended to: {output_file}")
    print(f"\nRun the pipeline to process them:")
    print(f"  localhost:7777 → Run Pipeline")
    print(f"\nNote: Processing {len(new_bookmarks)} URLs will take time and API costs.")
    print(f"Estimate: ${len(new_bookmarks) * 0.02:.2f} - ${len(new_bookmarks) * 0.05:.2f}")


if __name__ == "__main__":
    main()
