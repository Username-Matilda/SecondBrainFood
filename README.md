# Second Brain Food

**Auto-summarise tabs you want to explore but don't have time to read. Close them. Trust the system. Schedule time to review them. They'll be waiting for you, saved and tagged in your Obsidian vault**

A minimal pipeline for transforming browser tab anxiety into leanly captured knowledge. Closing feels like breaking the commitment. This system makes closure safe.
Note: this isn't a tool for organising tabs - it's really for people like me who get nerd-sniped 25 times a day by content that is probably really valuable and end up struggling with countless tabs open, only to try and bookmark or otherwise organise them and be really sad when the time doesn't ever materialise to read them all and all that potential cool knowledge is basically out of your reach.

Getting an LLM to summarise individual posts/book chapters etc and then manually saving them to Obsidian, adding tags etc. is too much friction for me. So here's an extremely simple pipeline that saves you that hassle.

---

## The Flow
```
Browser tab holds your attention hostage
              ↓
Alt+Shift+S → optional note → Enter
              ↓
Tab closes. You're free.
              ↓
localhost:7777 → click "Run Pipeline"
              ↓
Gears-level summary appears in Obsidian
              ↓
Knowledge transferred, distilled, organised. Debt cleared.
```

---

## What It Does

1. **Captures** — Browser extension grabs URL + title + page content + your note, closes the tab immediately
2. **Processes** — Pipeline fetches content (or uses captured content), sends to Claude for gears-level summarization
3. **Delivers** — Markdown files appear directly in your Obsidian vault
4. **Classifies** — Auto-tags from your personal taxonomy

"Gears-level" means: not "this article argues for X" but "the argument is A because B, mechanism C, predicts D." Knowledge you can run, not just reference.
"Your note" is any direction you want to give Claude as it summarises the page for you, e.g. 'compare this with xyz's stance on this topic'. It travels with the URL and shapes how the summary is generated. Empty is fine — it's optional context.

---

## Requirements

- Python 3.10+
- Chrome/Chromium browser
- Claude API key ([console.anthropic.com](https://console.anthropic.com))
- Obsidian (or any folder you want markdown files in - I created an INBOX folder)

---

## Installation

### 1. Clone and install dependencies
```bash
git clone https://github.com/YOUR_USERNAME/second-brain-food.git
cd second-brain-food
pip install anthropic trafilatura pdfplumber
```

### 2. Set environment variables

**Windows (permanent):**
- `Win + R` → `sysdm.cpl` → Advanced → Environment Variables
- Add under User variables:
  - `ANTHROPIC_API_KEY` = `sk-ant-your-key-here`
  - `OBSIDIAN_VAULT_PATH` = `C:\path\to\your\vault\Inbox`

**Mac/Linux:**
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
export OBSIDIAN_VAULT_PATH="/path/to/your/vault/Inbox"
```

### 3. Install browser extension

1. Open `chrome://extensions/`
2. Enable "Developer mode" (top right)
3. Click "Load unpacked"
4. Select the `tab-capture-extension/tab-capture-extension/` folder from this repo
5. Pin to toolbar

### 4. Start the server
```bash
python capture_server.py
```

Open `localhost:7777` — you should see the dashboard.

---

## Usage

### Capture
- Navigate to any page
- Press `Alt+Shift+S` (or click extension icon)
- Add optional note → Enter
- Tab closes. Capture confirmed.

### Process
- Open `localhost:7777`
- Click "Run Pipeline"
- Summaries appear in your Obsidian inbox

### Review
- Open Obsidian
- Review summaries in your inbox folder - tip: block a weekly time to review your summaries so they don't wind up adrift in oblivion
- Move keepers to permanent locations
- Delete or archive the rest

---

## Utilities

**convert_bookmarks.py** — Imports Chrome bookmark exports (HTML) into the capture queue. Useful for processing your existing bookmark backlog.

**lw_fetcher.py** — Optimises content extraction for sites where anti-scraping measures create friction (LessWrong, etc.). Falls back gracefully when standard fetching fails.

**pdf_handler.py** — Extracts text from PDF URLs (including arXiv papers). Integrated into the pipeline automatically.

---

## Tag Library

Create `tag_library.md` in your Obsidian vault's inbox folder. The pipeline reads it and auto-classifies content. I plan on using this in conjunction with the Mind Map Obs community plugin.

Format:
```markdown
## Domains

## Content Types

type/paper :: Academic paper
type/practical :: How-to, actionable advice
```

The `::` descriptions help Claude classify accurately. Edit as your knowledge structure evolves.

---

## Auto-Start (Windows)

The server should run invisibly on login.

1. Save `start_silent.vbs` to this folder
2. `Win + R` → `shell:startup` → Enter
3. Create shortcut to `start_silent.vbs`

Server now awakens with Windows. No terminal. No thought.

---

## Scheduled Pipeline Runs (Optional)

The dashboard gives you on-demand processing. But if you want captures processed automatically—say, every evening—Windows Task Scheduler provides a safety net.

### Setup (3 minutes)

1. Open **Task Scheduler** (search in Start menu)
2. Click **Create Basic Task**
3. Configure:
   - Name: `Second Brain Food - Daily Process`
   - Trigger: **Daily** → choose time (e.g., 6:00 PM)
   - Action: **Start a program**
     - Program: `python`
     - Arguments: `"C:\path\to\second-brain-food\summarize_pipeline.py"`
     - Start in: `C:\path\to\second-brain-food`
4. Click Finish

### The Result
```
Captures accumulate throughout the day
              ↓
6 PM: pipeline runs silently
              ↓
Morning: summaries waiting in Obsidian
```

You can still click "Run Pipeline" anytime for immediate processing. The scheduled task is a fallback—ensuring nothing lingers unprocessed.

### Mac/Linux Alternative

Add to crontab (`crontab -e`):
```bash
0 18 * * * cd /path/to/second-brain-food && python summarize_pipeline.py
```

---

## File Structure
```
second-brain-food/
├── capture_server.py      # Server + dashboard
├── summarize_pipeline.py  # Fetch → Claude → Obsidian
├── pdf_handler.py         # PDF text extraction
├── convert_bookmarks.py   # Chrome bookmark importer
├── lw_fetcher.py          # Optimised fetcher for tricky sites
├── start_server.bat       # Manual start (visible)
├── start_silent.vbs       # Auto-start (invisible)
├── tab-capture-extension/
│   └── tab-capture-extension/
│       ├── manifest.json
│       ├── popup.html
│       ├── popup.js
│       └── icons/
└── README.md
```

---

## Philosophy

Tabs are deferred decisions. Each open tab whispers "you should read this" while fragmenting your attention across dozens of uncommitted threads.

The solution isn't discipline. It's infrastructure.

Capture creates a trusted container. The tab can close because the system holds its essence. The pipeline transforms that essence into transferable knowledge—not a bookmark you'll never revisit, but a summary you can actually use.

Close tabs. Clear mind. Trust the process.

---

## Credits

Built with [Claude](https://anthropic.com) for the thinking, [Trafilatura](https://github.com/adbar/trafilatura) for the extraction, and a philosophy that friction is the enemy of action.

---

## License

MIT. Use freely to empower yourself to be wiser and better informed, then go help save the world!