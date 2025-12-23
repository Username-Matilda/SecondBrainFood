#!/usr/bin/env python3
"""
Second Brain Food - Unified Server
===================================
Capture server + web dashboard in one.

Open http://localhost:7777 for the control panel.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import subprocess
import sys
import threading
import warnings
from datetime import datetime, timezone
from pathlib import Path

warnings.filterwarnings("ignore", category=DeprecationWarning)

PORT = 7777
CAPTURE_FILE = Path(os.path.expanduser("~/captured_tabs.jsonl"))
PROCESSED_FILE = CAPTURE_FILE.with_suffix(".processed.jsonl")
SCRIPT_DIR = Path(__file__).parent

pipeline_status = {"running": False, "last_run": None, "last_result": None}


def count_pending():
    if not CAPTURE_FILE.exists():
        return 0
    
    captured = set()
    with open(CAPTURE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    captured.add(json.loads(line).get("url"))
                except:
                    pass
    
    processed = set()
    if PROCESSED_FILE.exists():
        with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        processed.add(json.loads(line).get("url"))
                    except:
                        pass
    
    return len(captured - processed)


def get_recent_captures(n=5):
    if not CAPTURE_FILE.exists():
        return []
    
    captures = []
    with open(CAPTURE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    captures.append(json.loads(line))
                except:
                    pass
    
    return captures[-n:][::-1]


def run_pipeline_async():
    global pipeline_status
    
    if pipeline_status["running"]:
        return False
    
    def _run():
        global pipeline_status
        pipeline_status["running"] = True
        pipeline_status["last_run"] = datetime.now().strftime("%H:%M:%S")
        
        try:
            result = subprocess.run(
                [sys.executable, str(SCRIPT_DIR / "summarize_pipeline.py")],
                capture_output=True,
                text=True,
                timeout=300
            )
            pipeline_status["last_result"] = "success" if result.returncode == 0 else "error"
        except subprocess.TimeoutExpired:
            pipeline_status["last_result"] = "timeout"
        except Exception as e:
            pipeline_status["last_result"] = f"error: {e}"
        finally:
            pipeline_status["running"] = False
    
    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return True


DASHBOARD_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Second Brain Food</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0a0a0a;
            color: #e0e0e0;
            min-height: 100vh;
            padding: 40px 20px;
        }
        
        .container { max-width: 600px; margin: 0 auto; }
        
        h1 {
            font-size: 24px;
            font-weight: 400;
            margin-bottom: 40px;
            color: #fff;
        }
        
        .card {
            background: #141414;
            border: 1px solid #222;
            border-radius: 8px;
            padding: 24px;
            margin-bottom: 20px;
        }
        
        .status-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .status-label { color: #888; font-size: 14px; }
        
        .status-value {
            font-size: 32px;
            font-weight: 600;
            color: #4ade80;
        }
        
        .status-value.zero { color: #666; }
        
        .btn {
            display: inline-block;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 500;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.15s;
        }
        
        .btn-primary {
            background: #4a9eff;
            color: #000;
            width: 100%;
        }
        
        .btn-primary:hover { background: #6bb3ff; }
        .btn-primary:disabled { 
            background: #333; 
            color: #666; 
            cursor: not-allowed;
        }
        
        .btn-running { background: #333; color: #4ade80; }
        
        .recent-title {
            font-size: 14px;
            color: #888;
            margin-bottom: 16px;
        }
        
        .capture-item {
            padding: 12px 0;
            border-bottom: 1px solid #222;
        }
        
        .capture-item:last-child { border-bottom: none; }
        
        .capture-title {
            font-size: 14px;
            color: #e0e0e0;
            margin-bottom: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .capture-meta { font-size: 12px; color: #555; }
        
        .footer {
            text-align: center;
            margin-top: 40px;
            font-size: 12px;
            color: #444;
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            margin-left: 8px;
        }
        
        .status-badge.success { background: #1a3a1a; color: #4ade80; }
        .status-badge.error { background: #3a1a1a; color: #f87171; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Second Brain Food</h1>
        
        <div class="card">
            <div class="status-row">
                <span class="status-label">Pending captures</span>
                <span class="status-value" id="pendingCount">-</span>
            </div>
            <button class="btn btn-primary" id="runBtn" onclick="runPipeline()">
                Run Pipeline
            </button>
            <div id="statusMsg" style="margin-top: 12px; font-size: 13px; color: #888;"></div>
        </div>
        
        <div class="card">
            <div class="recent-title">Recent captures</div>
            <div id="recentList">Loading...</div>
        </div>
        
        <div class="footer">
            Capture: Alt+Shift+S
        </div>
    </div>
    
    <script>
        async function fetchStatus() {
            try {
                const res = await fetch('/status');
                const data = await res.json();
                
                document.getElementById('pendingCount').textContent = data.pending;
                document.getElementById('pendingCount').className = 
                    'status-value' + (data.pending === 0 ? ' zero' : '');
                
                const btn = document.getElementById('runBtn');
                const msg = document.getElementById('statusMsg');
                
                if (data.pipeline_running) {
                    btn.disabled = true;
                    btn.textContent = 'Running...';
                    btn.className = 'btn btn-running';
                } else {
                    btn.disabled = false;
                    btn.textContent = 'Run Pipeline';
                    btn.className = 'btn btn-primary';
                }
                
                if (data.last_run) {
                    let badge = '';
                    if (data.last_result === 'success') {
                        badge = '<span class="status-badge success">done</span>';
                    } else if (data.last_result && data.last_result !== 'success') {
                        badge = '<span class="status-badge error">error</span>';
                    }
                    msg.innerHTML = 'Last run: ' + data.last_run + badge;
                }
                
                const list = document.getElementById('recentList');
                if (data.recent.length === 0) {
                    list.innerHTML = '<div style="color: #555; font-size: 13px;">No captures yet</div>';
                } else {
                    list.innerHTML = data.recent.map(c => `
                        <div class="capture-item">
                            <div class="capture-title">${escapeHtml(c.title || c.url)}</div>
                            <div class="capture-meta">${c.note || 'No note'}</div>
                        </div>
                    `).join('');
                }
            } catch (e) {
                console.error(e);
            }
        }
        
        async function runPipeline() {
            document.getElementById('runBtn').disabled = true;
            document.getElementById('runBtn').textContent = 'Starting...';
            await fetch('/run', { method: 'POST' });
            setTimeout(fetchStatus, 500);
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        fetchStatus();
        setInterval(fetchStatus, 2000);
    </script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        if self.path == '/' or self.path == '/dashboard':
            self._send_html(DASHBOARD_HTML)
        elif self.path == '/status':
            self._send_json({
                "pending": count_pending(),
                "recent": get_recent_captures(5),
                "pipeline_running": pipeline_status["running"],
                "last_run": pipeline_status["last_run"],
                "last_result": pipeline_status["last_result"]
            })
        else:
            self._send_json({"error": "Not found"}, 404)
    
    def do_POST(self):
        if self.path == '/capture':
            self._handle_capture()
        elif self.path == '/run':
            started = run_pipeline_async()
            self._send_json({"started": started})
        else:
            self._send_json({"error": "Not found"}, 404)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()
    
    def _handle_capture(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))
            
            entry = {
                "url": data.get("url"),
                "title": data.get("title", ""),
                "note": data.get("note", ""),
                "captured_at": datetime.now(timezone.utc).isoformat()
            }
            
            with open(CAPTURE_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
            
            print(f"  + {entry['title'][:50]}...")
            self._send_json({"status": "ok"})
            
        except Exception as e:
            self._send_json({"error": str(e)}, 500)
    
    def _send_html(self, html):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def _send_json(self, data, status=200):
        self.send_response(status)
        self._cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def _cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def log_message(self, *args):
        pass


def main():
    print(f"""
  Second Brain Food
  
  Dashboard:  http://localhost:{PORT}
  Captures:   {CAPTURE_FILE}

  Ctrl+C to stop
""")
    
    server = HTTPServer(('localhost', PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.")
        server.shutdown()


if __name__ == '__main__':
    main()
