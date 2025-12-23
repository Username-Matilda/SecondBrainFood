# Auto-Start Setup

The server awakens with Windows. No terminal. No intervention.

---

## Setup (2 minutes)

**Step 1:** Save `start_silent.vbs` to your Second Brain Food folder.

**Step 2:** Press `Win + R`, type `shell:startup`, Enter.

**Step 3:** In that folder, right-click → New → Shortcut → browse to:
```
C:\Users\minad\Documents\Tools\Second Brain Food\start_silent.vbs
```
Name it "Second Brain Food". Done.

---

## Verify

Restart your computer (or double-click `start_silent.vbs` to test now).

Open `localhost:7777`. Dashboard loads = server running.

---

## Managing the Invisible Server

| Action | Method |
|--------|--------|
| Check status | Open localhost:7777 |
| Stop | Task Manager → End `pythonw` process |
| Start manually | Double-click `start_silent.vbs` |

---

## If Dashboard Won't Load

Open `start_silent.vbs` in Notepad. Verify path matches your actual folder:
```vbs
WshShell.CurrentDirectory = "C:\Users\minad\Documents\Tools\Second Brain Food"
```
