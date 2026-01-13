
import sys
import os
import traceback

# Add project root to sys.path
sys.path.append(os.getcwd())

print("Attempting to import services.deploy...")

try:
    from services import deploy
    print("Successfully imported services.deploy")
except Exception:
    traceback.print_exc()
    sys.exit(1)
