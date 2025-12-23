' Second Brain Food - Silent Launcher
' This script starts the capture server without a visible window.
' Place shortcut to this file in shell:startup folder.

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\minad\Documents\Tools\Second Brain Food"
WshShell.Run "pythonw capture_server.py", 0, False
