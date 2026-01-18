@echo off
title Unk Trader - Micro Scalping Mode
mode con: cols=165 lines=50
cd /d "c:\Users\super\Watchtower\unk-app-ai"

:loop
echo [ %TIME% ] Starting Unk Trader...
venv\Scripts\python.exe scripts\unk_trader_cli.py
echo.
echo [ %TIME% ] ⚠️ Bot stopped or crashed!
echo Restarting in 10 seconds... (Press Ctrl+C to abort)
timeout /t 10
goto loop
