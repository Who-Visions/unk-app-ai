$env:PAPER_TRADE = "false"
Write-Host "WARNING: STARTING LIVE PENNY SHAVER (SNOWBALL MODE)" -ForegroundColor Green
Write-Host "Mode: REINVEST PROFIT (No BTC Sweep)"
Write-Host "Ensuring we are in the correct directory..."
cd $PSScriptRoot

Write-Host "Launching Bot..."
./venv/Scripts/python.exe trading/bots/penny_shaver_snowball.py
