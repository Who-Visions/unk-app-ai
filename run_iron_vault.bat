@echo off
TITLE Penny Shaver - IRON VAULT (BTC Sweep)
cd /d "%~dp0"
echo ===================================================
echo [IRON VAULT MODE] Starting Penny Shaver...
echo WARNING: Lives trades enabled. Profit sweeps to BTC.
echo ===================================================
call venv\Scripts\activate.bat
set PAPER_TRADE=false
python trading\bots\penny_shaver.py
pause
