@echo off
title Unk Trader - Micro Scalping Mode
mode con: cols=120 lines=50
cd /d "c:\Users\super\Watchtower\unk-app-ai"
cmd /k "venv\Scripts\python.exe scripts\unk_trader_cli.py"
