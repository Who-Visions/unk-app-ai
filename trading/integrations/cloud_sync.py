import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime

# Initialize Firebase
# We check if already initialized to avoid errors on reload
if not firebase_admin._apps:
    try:
        # Expected from Environment Variables
        cred_dict = {
            "type": "service_account",
            "project_id": os.environ.get("FIREBASE_ADMIN_PROJECT_ID"),
            "private_key_id": "hardcoded_or_ignored", # Not strictly needed often
            "private_key": os.environ.get("FIREBASE_ADMIN_PRIVATE_KEY", "").replace("\\n", "\n"),
            "client_email": os.environ.get("FIREBASE_ADMIN_CLIENT_EMAIL"),
            "client_id": "ignored",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/" + os.environ.get("FIREBASE_ADMIN_CLIENT_EMAIL", "")
        }
        
        # Only initialize if we have the key
        if cred_dict["private_key"]:
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("[CloudSync] Firebase Connected to 'who-visions-tester'")
        else:
            print("[CloudSync] No Private Key found. Cloud sync disabled.")

    except Exception as e:
        print(f"[CloudSync] Init Failed: {e}")

db = firestore.client() if firebase_admin._apps else None

def push_state(state):
    """
    Push the current trading state to Firestore.
    Collection: 'trading_bot'
    Doc: 'global_state'
    """
    if not db:
        return

    try:
        # We need to sanitize state for Firestore (no floats like 4e-06 if possible, but Firestore handles floats well)
        # We add a timestamp
        data = state.copy()
        data["last_synced"] = datetime.now().isoformat()
        
        # Fire and forget (or await if async)
        # Using the synchronous client here for simplicity in this thread
        db.collection("trading_bot").document("global_state").set(data)
        # print("☁️ Synced") # Too noisy
    except Exception as e:
        # print(f"☁️ Sync Error: {e}") 
        pass
