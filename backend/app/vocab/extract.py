import json
import os
from dataclasses import dataclass
from fugashi import Tagger

_tagger = Tagger()

_CONTENT_POS = {"名詞", "動詞", "形容詞", "形状詞", "副詞"}
_SKIP_NOUN_SUBTYPES = {"数詞"}


@dataclass
class VocabItem:
    word: str       # dictionary (lemma) form
    reading: str    # katakana reading, from fugashi (kanaBase)
    level: str      # N5..N1, or "unknown" — from JLPT table


def load_jlpt_table(path: str) -> dict[str, dict]:
    with open(path, encoding="utf-8") as f:
        entries = json.load(f)
    # We only need the level now; reading comes from fugashi. But we keep the
    # table's reading too as a fallback in case fugashi ever yields an empty.
    return {e["word"]: {"reading": e["reading"], "level": e["level"]} for e in entries}


def tokenize_content_words(text: str) -> list[tuple[str, str]]:
    """Return (lemma, reading) pairs for content words.

    Reading comes straight from fugashi's kanaBase field — the katakana reading
    of the dictionary form. This means EVERY token gets a reading, including
    words absent from the JLPT table (which are often the most useful ones).
    """
    results: list[tuple[str, str]] = []
    for word in _tagger(text):
        feat = word.feature
        pos1 = feat.pos1
        if pos1 not in _CONTENT_POS:
            continue
        if pos1 == "名詞" and feat.pos2 in _SKIP_NOUN_SUBTYPES:
            continue

        lemma = feat.lemma if feat.lemma else word.surface
        lemma = lemma.split("-")[0]

        # kanaBase = katakana reading of the dictionary form. Fall back through
        # kana, then empty string, since UniDic occasionally emits "*".
        reading = feat.kanaBase or feat.kana or ""
        if reading == "*":
            reading = ""

        results.append((lemma, reading))
    return results


def extract_vocab(text: str, jlpt_table: dict[str, dict]) -> list[VocabItem]:
    pairs = tokenize_content_words(text)

    # Deduplicate by lemma, keeping the first reading seen for each.
    seen: dict[str, str] = {}
    for lemma, reading in pairs:
        if lemma not in seen:
            seen[lemma] = reading

    items: list[VocabItem] = []
    for lemma, reading in seen.items():
        entry = jlpt_table.get(lemma)
        level = entry["level"] if entry else "unknown"
        # Reading from fugashi; if somehow empty, fall back to the table's.
        if not reading and entry:
            reading = entry["reading"]
        items.append(VocabItem(word=lemma, reading=reading, level=level))
    return items