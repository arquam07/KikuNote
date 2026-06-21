import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.pipeline import process_audio

load_dotenv()

PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
REGION = os.getenv("STT_REGION", "asia-northeast1")

if __name__ == "__main__":
    audio_path = sys.argv[1] if len(sys.argv) > 1 else "recordings/Recording.mp3"

    print(f"Processing {audio_path}...\n")
    result = process_audio(audio_path, PROJECT_ID, REGION)

    print("--- Transcript ---")
    print(result["transcript"])
    print("\n--- Vocab ---")
    print(f"{'WORD':<10} {'READING':<12} LEVEL")
    print("-" * 34)
    for v in result["vocab"]:
        print(f"{v['word']:<10} {v['reading']:<12} {v['level']}")
    print(f"\n{len(result['vocab'])} unique content words.")