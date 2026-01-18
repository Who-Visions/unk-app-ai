import subprocess
import time
import sys
import os
from datetime import datetime

# Path to the actual bot script
BOT_SCRIPT = r"scripts/unk_trader_cli.py"
# Python executable (use the current venv python)
PYTHON_EXE = sys.executable

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [SUPERVISOR] {msg}")

def run_bot():
    """Runs the bot as a subprocess and monitors it."""
    while True:
        log(f"🚀 Launching Bot: {BOT_SCRIPT}")
        
        # Prepare environment with PYTHONPATH
        env = os.environ.copy()
        env["PYTHONPATH"] = os.getcwd()
        
        # Start the process
        process = subprocess.Popen([PYTHON_EXE, BOT_SCRIPT], env=env)
        
        # Wait for it to finish
        exit_code = process.wait()
        
        log(f"⚠️ Bot exited with code: {exit_code}")
        
        # Logic for restarts
        # 0 = Clean exit (Graceful Restart Requested or User stopped)
        # 1 = Crash / Error
        
        if exit_code == 0:
            log("✅ Clean exit. Restarting in 5 seconds (Graceful Reset)...")
        else:
            log("❌ Crash detected! Restarting in 10 seconds (Crash Recovery)...")
            time.sleep(5)  # Extra wait for crash dampening
            
        time.sleep(5)

if __name__ == "__main__":
    if not os.path.exists(BOT_SCRIPT):
        log(f"❌ Error: Script not found at {BOT_SCRIPT}")
        sys.exit(1)
        
    try:
        run_bot()
    except KeyboardInterrupt:
        log("🛑 Supervisor Stopped by User.")
        sys.exit(0)
