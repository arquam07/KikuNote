import os, sys
from dotenv import load_dotenv
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

load_dotenv()

from app.llm.analyze import summarize, filter_useful_words


SAMPLE_TRANSCRIPT = "今日の会議で新しいプロジェクトの予算について話しました。来週までに資料を準備する必要があります。"
SAMPLE_WORDS = [
    {"word": "会議", "reading": "カイギ", "level": "N4"},
    {"word": "予算", "reading": "ヨサン", "level": "N2"},
    {"word": "する", "reading": "", "level": "unknown"},
    {"word": "資料", "reading": "シリョウ", "level": "N3"},
]

if __name__ == "__main__":
    summary, su = summarize(SAMPLE_TRANSCRIPT)
    print("SUMMARY:", summary)
    print("  tokens:", su)

    kept, fu = filter_useful_words(SAMPLE_WORDS)
    print("\nKEPT WORDS:")
    for w in kept:
        print(f"  {w['word']} ({w['level']}) — {w['gloss']}")
    print("  tokens:", fu)