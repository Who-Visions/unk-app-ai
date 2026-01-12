"""
Startup Verification Script
===========================
Mimics the production startup import sequence to catch errors early.
"""
import sys
import os
import traceback
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("startup_check")

# Ensure project root is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

print(f"Project Root: {project_root}")
print(f"Sys Path: {sys.path}")

def verify_imports():
    """Attempt to import critical modules."""
    modules_to_check = [
        "routers.config",
        "routers.dependencies",
        "routers.core",
        "routers.models",
        "routers.chat",
        "routers.a2a",
        "routers.tools",
        "routers.lore",
        "routers.orchestrator",
        "routers.auth",
        "routers.threads",
        "services.deploy",
        "gemini_agent.models_spec"
    ]

    all_passed = True
    print("\n--- Starting Import Checks ---")

    for module in modules_to_check:
        try:
            __import__(module)
            print(f"✅ Imported: {module}")
        except ImportError as e:
            print(f"❌ Failed to import {module}: {e}")
            traceback.print_exc()
            all_passed = False
        except Exception as e:
            print(f"❌ Error during import of {module}: {e}")
            traceback.print_exc()
            all_passed = False

    if all_passed:
        print("\n✅ All critical checks passed.")
        sys.exit(0)
    else:
        print("\n❌ Startup verification failed.")
        sys.exit(1)

if __name__ == "__main__":
    verify_imports()
