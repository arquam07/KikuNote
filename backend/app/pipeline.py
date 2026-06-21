import os
from app.audio.transcribe import transcribe_file
from app.vocab.extract import load_jlpt_table, extract_vocab, VocabItem

# Resolve the JLPT table path once, relative to this file, so it works
# no matter what directory the process is launched from.
_JLPT_PATH = os.path.join(os.path.dirname(__file__), "vocab", "jlpt_vocab.json")
_jlpt_table = load_jlpt_table(_JLPT_PATH)


def process_audio(audio_path: str, project_id: str, region: str) -> dict:
    """Full Phase-1 core: audio file -> transcript + leveled vocab list.

    Returns a plain dict so this is trivially serializable to JSON later
    by FastAPI. No web concepts in here — this function knows nothing about
    HTTP, which is exactly why it's testable on its own.
    """
    transcript = transcribe_file(audio_path, project_id, region)

    vocab_items = extract_vocab(transcript, _jlpt_table)

    return {
        "transcript": transcript,
        "vocab": [
            {"word": v.word, "reading": v.reading, "level": v.level}
            for v in vocab_items
        ],
    }