"""One-time converter: Bluskyo JLPT JSON -> KikuNote's flat jlpt_vocab.json.

Bluskyo shape:   { "嗚呼": [ {"reading": " /ああ/", "level": 1}, ... ], ... }
KikuNote shape:  [ {"word": "嗚呼", "reading": "アア", "level": "N1"}, ... ]

Transforms applied:
  - integer level 1..5  ->  "N1".."N5"  (1 = hardest, 5 = easiest)
  - hiragana reading     ->  katakana    (to match fugashi's kanaBase output)
  - multi-level word     ->  keep EASIEST level (max int = lowest difficulty)
"""
import json
import sys

# --- hiragana -> katakana ---
# Every hiragana code point sits exactly 0x60 below its katakana twin.
# Converting here means the JLPT readings match fugashi's katakana output,
# so a fallback reading never looks out of place.
def hira_to_kata(s: str) -> str:
    out = []
    for ch in s:
        code = ord(ch)
        # hiragana block U+3041..U+3096
        if 0x3041 <= code <= 0x3096:
            out.append(chr(code + 0x60))
        else:
            out.append(ch)
    return "".join(out)


def level_int_to_str(n: int) -> str:
    return f"N{n}"


def convert(src_path: str, dst_path: str) -> None:
    with open(src_path, encoding="utf-8") as f:
        raw = json.load(f)

    out = []
    multi_level = 0
    for word, entries in raw.items():
        if not entries:
            continue
        # A word may appear at several levels. Keep the EASIEST (max int).
        # Among entries at that easiest level, take the first reading.
        easiest = max(e["level"] for e in entries)
        if len({e["level"] for e in entries}) > 1:
            multi_level += 1
        reading_hira = next(e["reading"] for e in entries if e["level"] == easiest)
        out.append({
            "word": word,
            "reading": hira_to_kata(reading_hira.strip("/ ")),  # strip stray /.../ if present
            "level": level_int_to_str(easiest),
        })

    with open(dst_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    # Report so you can sanity-check the conversion.
    from collections import Counter
    dist = Counter(item["level"] for item in out)
    print(f"Wrote {len(out)} words to {dst_path}")
    print(f"Words appearing at multiple levels (kept easiest): {multi_level}")
    print("Level distribution:", dict(sorted(dist.items())))


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "jlpt_source.json"
    dst = sys.argv[2] if len(sys.argv) > 2 else "jlpt_vocab.json"
    convert(src, dst)