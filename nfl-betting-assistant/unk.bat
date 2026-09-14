@echo off
rem Talk to Unk. Double-click for chat, or: unk "knicks ats 2025"
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0src"
python unk_cli.py %*
