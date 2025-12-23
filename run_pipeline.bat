@echo off
REM Second Brain Food - Run Summarization Pipeline
REM Processes captured tabs and generates Obsidian summaries

cd /d "%~dp0"

REM Check if environment variables are set
if "%ANTHROPIC_API_KEY%"=="" (
    echo ERROR: ANTHROPIC_API_KEY not set.
    echo.
    echo Run this in PowerShell first:
    echo   $env:ANTHROPIC_API_KEY = "sk-ant-your-key"
    echo.
    echo Or set it permanently in Windows Environment Variables.
    pause
    exit /b 1
)

if "%OBSIDIAN_VAULT_PATH%"=="" (
    echo ERROR: OBSIDIAN_VAULT_PATH not set.
    echo.
    echo Run this in PowerShell first:
    echo   $env:OBSIDIAN_VAULT_PATH = "C:\path\to\vault\Inbox"
    echo.
    echo Or set it permanently in Windows Environment Variables.
    pause
    exit /b 1
)

echo.
echo Running Second Brain Food Pipeline...
echo.
python summarize_pipeline.py
echo.
pause
