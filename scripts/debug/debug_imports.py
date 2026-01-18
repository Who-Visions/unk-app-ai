import sys
print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")

try:
    import youtube_transcript_api
    print(f"youtube_transcript_api: {youtube_transcript_api.__version__} (OK)")
except ImportError as e:
    print(f"youtube_transcript_api: FAILED ({e})")
except Exception as e:
    print(f"youtube_transcript_api: FAILED with generic error ({e})")

try:
    import yt_dlp
    print(f"yt_dlp: {yt_dlp.version.__version__} (OK)")
except ImportError as e:
    print(f"yt_dlp: FAILED ({e})")
except Exception as e:
    print(f"yt_dlp: FAILED with generic error ({e})")
