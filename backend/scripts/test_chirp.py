import os
import sys
from dotenv import load_dotenv

# Make the app package importable when running this script directly.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.audio.transcribe import transcribe_file

load_dotenv()

PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
REGION = os.getenv("STT_REGION", "us")

if __name__ == "__main__":
    audio_path = sys.argv[1] if len(sys.argv) > 1 else "resources/sample_ja.wav"

    print(f"Transcribing {audio_path} with chirp_3 in region {REGION}...")
    transcript = transcribe_file(audio_path, PROJECT_ID, REGION)
    print("\n--- Transcript ---")
    print(transcript if transcript else "(empty — check audio/region/language)")