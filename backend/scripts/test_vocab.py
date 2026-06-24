import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.vocab.extract import load_jlpt_table, extract_vocab

JLPT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "app", "vocab", "JLPT_vocab_final.json"
)

# A hand-written sample transcript so we don't burn Chirp calls while testing
# this stage. Swap in a real Chirp transcript once this works.
SAMPLE = "私たちは1990年という IT 分野の幕開けとも言える時期から IT ビジネス支援事業としてデジタルコンテンツを中心としたユニークなサービスを提供しています。現在、数多くの実績を誇る国内屈指のインフォメーションインテグレータです。企業に求められる様々な要件について顧客企業様の経営戦略に基づく包括的なサービスを提供しています"

if __name__ == "__main__":
    table = load_jlpt_table(JLPT_PATH)
    print(f"Loaded {len(table)} JLPT entries.\n")

    items = extract_vocab(SAMPLE, table)
    print(f"{'WORD':<8} {'READING':<12} LEVEL")
    print("-" * 30)
    for it in items:
        print(f"{it.word:<8} {it.reading:<12} {it.level}")