#!/usr/bin/env python3
"""
Second Brain Food - Summarization Pipeline (v3)
================================================
Clean output. Keyword filenames. No redundancy.
"""

import os
import sys
import json
import re
import warnings
from datetime import datetime, timezone
from pathlib import Path

warnings.filterwarnings("ignore", category=DeprecationWarning)

try:
    import anthropic
except ImportError:
    print("Missing 'anthropic'. Run: python -m pip install anthropic")
    sys.exit(1)

try:
    import trafilatura
except ImportError:
    print("Missing 'trafilatura'. Run: python -m pip install trafilatura")
    sys.exit(1)


def get_config():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set.")
        sys.exit(1)
    
    vault_path = os.environ.get("OBSIDIAN_VAULT_PATH")
    if not vault_path:
        print("ERROR: OBSIDIAN_VAULT_PATH not set.")
        sys.exit(1)
    
    vault_path = Path(vault_path)
    if not vault_path.exists():
        print(f"ERROR: Path does not exist: {vault_path}")
        sys.exit(1)
    
    captured_file = Path(os.environ.get(
        "CAPTURED_TABS_FILE", 
        os.path.expanduser("~/captured_tabs.jsonl")
    ))
    
    script_dir = Path(__file__).parent
    tag_library_path = None
    if (script_dir / "tag_library.md").exists():
        tag_library_path = script_dir / "tag_library.md"
    elif (vault_path / "tag_library.md").exists():
        tag_library_path = vault_path / "tag_library.md"
    
    return {
        "api_key": api_key,
        "vault_path": vault_path,
        "captured_file": captured_file,
        "processed_file": captured_file.with_suffix(".processed.jsonl"),
        "tag_library_path": tag_library_path
    }


def load_tag_library(filepath: Path) -> str:
    if filepath and filepath.exists():
        return filepath.read_text(encoding="utf-8")
    return ""


def fetch_content(url: str) -> dict:
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return {"success": False, "error": "Could not download"}
        
        content = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=True,
            no_fallback=False
        )
        metadata = trafilatura.extract_metadata(downloaded)
        
        if not content or len(content.strip()) < 100:
            return {"success": False, "error": "No content extracted"}
        
        return {
            "success": True,
            "content": content,
            "title": metadata.title if metadata else None,
            "author": metadata.author if metadata else None,
            "date": metadata.date if metadata else None,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


SUMMARY_PROMPT = """Create a gears-level summary. Goal: knowledge transfer—reader can run the model themselves.

REQUIREMENTS:
1. Extract ACTUAL ARGUMENTS, not meta-descriptions
   - BAD: "The author argues for X"
   - GOOD: "The argument: A because B. Mechanism: C. Predicts: D."

2. Structure:
   - Core thesis (1-2 sentences)
   - Key mechanisms (how does it work?)
   - Strongest evidence/example
   - Implications (what does this predict?)
   - Breaking conditions (when is this wrong?)

3. For non-content pages (applications, tools):
   - What is it?
   - Requirements/deadlines
   - Action required?

DO NOT include author/date/source header—that's in frontmatter.
DO NOT repeat tags in the summary body.
Keep it 200-400 words. Dense. No fluff.

{tag_instructions}

FORMAT:
TAGS: tag1, tag2, tag3
---
[Summary in markdown, starting directly with core thesis]

---
USER NOTE: {note}
URL: {url}
CONTENT:
{content}
"""

TAG_INSTRUCTIONS = """
Select 3-5 tags from this library. Use exact names.

AVAILABLE TAGS:
{tag_library}
"""


def generate_summary(client, url: str, content: str, note: str, tag_library: str) -> dict:
    max_chars = 100000
    if len(content) > max_chars:
        content = content[:max_chars] + "\n[truncated]"
    
    tag_instructions = ""
    if tag_library.strip():
        tag_instructions = TAG_INSTRUCTIONS.format(tag_library=tag_library)
    
    prompt = SUMMARY_PROMPT.format(
        note=note or "(none)",
        url=url,
        content=content,
        tag_instructions=tag_instructions
    )
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}]
    )
    
    response = message.content[0].text
    tags = []
    summary = response
    
    if response.startswith("TAGS:"):
        lines = response.split("\n", 2)
        tag_line = lines[0].replace("TAGS:", "").strip()
        tags = [t.strip() for t in tag_line.split(",") if t.strip()]
        if "---" in response:
            summary = response.split("---", 1)[1].strip()
    
    return {"summary": summary, "tags": tags}


def extract_keywords(title: str, max_words: int = 4) -> str:
    """Extract meaningful keywords from title for filename."""
    if not title:
        return "untitled"
    
    # Remove common filler words
    stopwords = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'this', 'that', 'these',
        'those', 'it', 'its', 'as', 'if', 'how', 'why', 'what', 'when', 'where',
        'who', 'which', 'your', 'my', 'our', 'their', 'his', 'her', 'we', 'you',
        'they', 'i', 'me', 'us', 'him', 'them', 'about', 'into', 'through',
        'during', 'before', 'after', 'above', 'below', 'between', 'under',
        'again', 'further', 'then', 'once', 'here', 'there', 'all', 'each',
        'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
        'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'can'
    }
    
    # Clean and split
    clean = re.sub(r'[<>:"/\\|?*\-–—]', ' ', title)
    words = clean.lower().split()
    
    # Filter to meaningful words
    keywords = [w for w in words if w not in stopwords and len(w) > 2]
    
    # Take first N keywords, capitalize
    selected = keywords[:max_words]
    if not selected:
        selected = words[:max_words]  # fallback to original words
    
    return '-'.join(word.capitalize() for word in selected)


def slugify(text: str) -> str:
    text = re.sub(r'[<>:"/\\|?*]', '', text)
    text = re.sub(r'\s+', '-', text.strip())
    text = re.sub(r'-+', '-', text)
    return text.strip('-')[:60] or "untitled"


def write_summary(vault_path: Path, url: str, title: str, summary: str, 
                  tags: list, metadata: dict, note: str):
    # Keyword-based filename
    filename = extract_keywords(title) + ".md"
    filepath = vault_path / filename
    
    # Handle duplicates
    counter = 1
    base_name = extract_keywords(title)
    while filepath.exists():
        filename = f"{base_name}-{counter}.md"
        filepath = vault_path / filename
        counter += 1
    
    # Minimal frontmatter
    fm = ["---", f'url: "{url}"']
    if metadata.get("author"):
        fm.append(f'author: "{metadata["author"]}"')
    if metadata.get("date"):
        fm.append(f'date: "{metadata["date"]}"')
    if note:
        fm.append(f'note: "{note.replace(chr(34), chr(39))}"')
    fm.append("---")
    
    # Tags at bottom, not in frontmatter (cleaner for reading)
    tag_line = " ".join(f"#{t}" for t in ["inbox"] + tags) if tags else "#inbox"
    
    doc = f"""{chr(10).join(fm)}

# {title or "Untitled"}

{summary}

---
{tag_line}
*Source: {url}*
"""
    
    filepath.write_text(doc, encoding="utf-8")
    return filepath


def load_captured(filepath: Path) -> list:
    if not filepath.exists():
        return []
    tabs = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    tabs.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return tabs


def load_processed(filepath: Path) -> set:
    if not filepath.exists():
        return set()
    urls = set()
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    urls.add(json.loads(line).get("url"))
                except json.JSONDecodeError:
                    continue
    return urls


def mark_processed(filepath: Path, url: str, status: str):
    entry = {"url": url, "status": status, "at": datetime.now(timezone.utc).isoformat()}
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def run():
    print("\n  Second Brain Food v3\n")
    
    config = get_config()
    print(f"  From: {config['captured_file']}")
    print(f"  To:   {config['vault_path']}")
    
    tag_library = ""
    if config["tag_library_path"]:
        tag_library = load_tag_library(config["tag_library_path"])
        print(f"  Tags: {config['tag_library_path']}")
    print()
    
    client = anthropic.Anthropic(api_key=config["api_key"])
    
    all_tabs = load_captured(config["captured_file"])
    processed = load_processed(config["processed_file"])
    pending = [t for t in all_tabs if t.get("url") not in processed]
    
    if not pending:
        print("  Nothing to process.")
        return
    
    print(f"  Processing {len(pending)} capture(s)...\n")
    
    for i, tab in enumerate(pending, 1):
        url = tab.get("url", "")
        title = tab.get("title", "Untitled")
        note = tab.get("note", "")
        
        print(f"  [{i}/{len(pending)}] {title[:50]}...")
        
        fetched = fetch_content(url)
        if not fetched["success"]:
            print(f"    ✗ {fetched['error']}")
            mark_processed(config["processed_file"], url, f"failed: {fetched['error']}")
            continue
        
        if fetched.get("title") and len(fetched["title"]) > len(title):
            title = fetched["title"]
        
        metadata = {"author": fetched.get("author"), "date": fetched.get("date")}
        
        try:
            result = generate_summary(client, url, fetched["content"], note, tag_library)
            if result["tags"]:
                print(f"    → {', '.join(result['tags'])}")
        except Exception as e:
            print(f"    ✗ API error: {e}")
            mark_processed(config["processed_file"], url, f"api_error: {e}")
            continue
        
        try:
            filepath = write_summary(
                config["vault_path"], url, title, 
                result["summary"], result["tags"], metadata, note
            )
            print(f"    ✓ {filepath.name}")
            mark_processed(config["processed_file"], url, "success")
        except Exception as e:
            print(f"    ✗ Write error: {e}")
            mark_processed(config["processed_file"], url, f"write_error: {e}")
        
        print()
    
    print("  Done.\n")


if __name__ == "__main__":
    run()
