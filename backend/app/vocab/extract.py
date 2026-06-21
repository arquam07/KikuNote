import json
import os
from dataclasses import dataclass
from fugashi import Tagger

# One Tagger instance, created once at import. Constructing it loads the
# dictionary into memory (~tens of MB), so you never want to do it per-call.
# This is the standard fugashi pattern.
_tagger = Tagger()

# POS tags (UniDic) we keep. fugashi's UniDic gives Japanese POS labels.
# 名詞 = noun, 動詞 = verb, 形容詞 = i-adjective, 形状詞 = na-adjective stem,
# 副詞 = adverb. Everything else (particles 助詞, auxiliaries 助動詞,
# punctuation 補助記号, symbols, etc.) is grammatical glue we drop.
_CONTENT_POS = {"名詞", "動詞", "形容詞", "形状詞", "副詞"}

# Sub-categories of 名詞 that are noise even though they're technically nouns:
# numbers, and proper-noun-ish junk. Kept minimal for now; tune later.
_SKIP_NOUN_SUBTYPES = {"数詞"}  # 数詞 = numeral


@dataclass
class VocabItem:
    word: str       # dictionary (lemma) form
    reading: str    # katakana reading from the lookup table
    level: str      # N5..N1, or "unknown"


def load_jlpt_table(path: str) -> dict[str, dict]:
    """Load jlpt_vocab.json into a dict keyed by word for O(1) lookup.

    Returns {word: {"reading": ..., "level": ...}}. Building a dict once
    turns the JLPT tagging step into a hash lookup instead of scanning a
    list per word.
    """
    with open(path, encoding="utf-8") as f:
        entries = json.load(f)
    return {e["word"]: {"reading": e["reading"], "level": e["level"]} for e in entries}


def tokenize_content_words(text: str) -> list[str]:
    """Tokenize Japanese text and return dictionary-form content words only.

    Steps per token:
      1. Read its POS from fugashi (word.feature.pos1 = top-level POS).
      2. Keep only content POS; drop particles, auxiliaries, punctuation.
      3. Use the lemma (dictionary form), not the surface form, so that
         しました -> する, 重要な -> 重要, etc.
    """
    lemmas: list[str] = []
    for word in _tagger(text):
        feat = word.feature
        pos1 = feat.pos1          # top-level POS, e.g. 名詞 / 動詞 / 助詞
        if pos1 not in _CONTENT_POS:
            continue
        # Skip numeral nouns and similar noise.
        if pos1 == "名詞" and feat.pos2 in _SKIP_NOUN_SUBTYPES:
            continue

        # feat.lemma is the dictionary form. It can be None for some tokens
        # (rare), so fall back to the surface string (word.surface).
        lemma = feat.lemma if feat.lemma else word.surface
        # UniDic lemmas sometimes carry a "-reading" suffix like 行く-ユク.
        # Strip anything after a hyphen to get the clean written form.
        lemma = lemma.split("-")[0]
        lemmas.append(lemma)
    return lemmas


def extract_vocab(text: str, jlpt_table: dict[str, dict]) -> list[VocabItem]:
    """Full pipeline: text -> deduplicated, JLPT-tagged content words."""
    lemmas = tokenize_content_words(text)

    # Deduplicate while preserving first-seen order (dict keeps insertion order).
    seen = list(dict.fromkeys(lemmas))

    items: list[VocabItem] = []
    for lemma in seen:
        entry = jlpt_table.get(lemma)
        if entry:
            items.append(VocabItem(word=lemma, reading=entry["reading"], level=entry["level"]))
        else:
            # Not in the table -> we do NOT guess. Mark unknown.
            items.append(VocabItem(word=lemma, reading="", level="unknown"))
    return items