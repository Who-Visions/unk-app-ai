@echo off
TITLE Penny Shaver - SNOWBALL MODE (Compound Growth)
cd /d "%~dp0"
echo ===================================================
echo [SNOWBALL MODE] Starting Penny Shaver...
echo WARNING: Lives trades enabled. Profits reinvested (No Sweep).
echo ===================================================
call venv\Scripts\activate.bat
set PAPER_TRADE=false
python trading\bots\penny_shaver_snowball.py
pause
