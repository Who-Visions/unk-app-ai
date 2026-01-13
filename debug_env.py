import sys
import os

print("--- SYS.PATH ---")
for p in sys.path:
    print(p)

print("\n--- IMPORT GOOGLE ---")
try:
    import google
    print(f"SUCCESS: google package at {google.__path__}")
except ImportError as e:
    print(f"FAIL: {e}")

print("\n--- IMPORT GOOGLE.GENAI ---")
try:
    from google import genai
    print(f"SUCCESS: google.genai imported")
except ImportError as e:
    print(f"FAIL: {e}")

print("\n--- PIP CHECK ---")
try:
    import pkg_resources
    # Filter for google packages
    google_pkgs = [p.project_name + " " + p.version for p in pkg_resources.working_set if "google" in p.project_name]
    print("Google packages:", google_pkgs)
except ImportError:
    print("pkg_resources not found")
