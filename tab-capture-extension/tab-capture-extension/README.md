# Tab Capture System

A two-part system for trusted tab capture:
1. **Browser Extension** — captures URLs with optional notes, closes tabs
2. **Local Server** — receives captures, writes to JSONL file

---

## Installation

### Step 1: Install the Browser Extension

1. Open Chrome and navigate to: `chrome://extensions/`

2. Enable **Developer mode** (toggle in top-right corner)

3. Click **Load unpacked**

4. Select the `tab-capture-extension` folder (the one containing `manifest.json`)

5. You should see "Tab Capture" appear in your extensions list

6. Pin it to your toolbar (click the puzzle piece icon → pin Tab Capture)

### Step 2: Start the Capture Server

Open a terminal and run:

```bash
python3 capture_server.py
```

You should see:

```
╭─────────────────────────────────────────╮
│         Tab Capture Server              │
╰─────────────────────────────────────────╯

Listening on: http://localhost:7777
Saving to:    /Users/yourname/captured_tabs.jsonl

Press Ctrl+C to stop.
```

**Keep this terminal open while you're capturing tabs.**

(Later we can set this to auto-start on login if you want.)

---

## Usage

### Capturing a Tab

1. Navigate to any page you want to capture

2. Either:
   - Click the Tab Capture icon in your toolbar, OR
   - Press `Ctrl+Shift+S` (or `Cmd+Shift+S` on Mac)

3. A small popup appears with the page title

4. Optionally type a note (examples below)

5. Press `Enter`

6. Tab closes. Green flash confirms success.

### Note Examples

| Note | Purpose |
|------|---------|
| *(empty)* | Just capture, summarize based on content |
| `for alignment research` | Adds context/tagging |
| `key claim: mesa-optimization` | Focuses summary on specific point |
| `deadline: march 15` | For applications/opportunities |
| `compare to Carlsmith's essays` | Notes connections |
| `skip summary, just archive` | (Future: different processing) |

---

## Where Do Captures Go?

Captures are appended to `~/captured_tabs.jsonl`

Each line is a JSON object:

```json
{"url": "https://...", "title": "Page Title", "note": "your note", "captured_at": "2025-12-23T14:30:00Z"}
```

---

## Troubleshooting

### "Could not connect to capture server"
The Python server isn't running. Start it with `python3 capture_server.py`

### Keyboard shortcut doesn't work
Chrome may have a conflict. Go to `chrome://extensions/shortcuts` to check or reassign.

### Extension doesn't appear
Make sure Developer Mode is enabled and you loaded the correct folder.

---

## Next Steps

This capture system feeds into the **summarization pipeline** (to be built next):

```
captured_tabs.jsonl
       │
       ▼
Pipeline reads new entries
       │
       ▼
Fetches content from each URL
       │
       ▼
Sends to Claude API for gears-level summary
       │
       ▼
Writes .md files to Obsidian vault
       │
       ▼
You review during weekly inbox processing
```

---

## Files in This Package

```
tab-capture-extension/
├── manifest.json      # Extension configuration
├── popup.html         # Capture UI
├── popup.js           # Capture logic
├── icon16.png         # Toolbar icon (small)
├── icon48.png         # Extension page icon
├── icon128.png        # Extension page icon (large)
├── capture_server.py  # Local server
└── README.md          # This file
```
