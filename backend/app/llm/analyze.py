import os
from pydantic import BaseModel
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# vertexai=True routes through Vertex using your ADC / service-account identity
# (the aiplatform.user role you already granted). No API key needed.
# location="global" maximizes model availability for these models.
_client = genai.Client(
    vertexai=True,
    project=os.environ["GOOGLE_CLOUD_PROJECT"],
    location=os.getenv("GEMINI_LOCATION", "global"),
)

_SUMMARY_MODEL = os.getenv("GEMINI_SUMMARY_MODEL", "gemini-2.5-flash")
_FILTER_MODEL = os.getenv("GEMINI_FILTER_MODEL", "gemini-2.5-flash-lite")


# --- Structured output schemas (Pydantic) ---
# Handing Gemini a schema makes it constrain generation to valid JSON matching
# this shape. No markdown fences, no "sometimes it adds prose" — the SDK parses
# it straight into these objects. This kills the whole JSON-parsing-bug class.

class SummaryResult(BaseModel):
    summary: str


class WordJudgment(BaseModel):
    word: str          # echoes back the lemma we sent
    keep: bool         # True = worth surfacing, False = noise/too common
    gloss: str         # short English meaning, "" if dropped


class FilterResult(BaseModel):
    judgments: list[WordJudgment]


def _usage(response) -> dict:
    """Pull token counts off the response. Present on every genai response.
    We return it so callers can log/inspect; we do NOT build accounting here."""
    u = response.usage_metadata
    return {
        "input_tokens": u.prompt_token_count,
        "output_tokens": u.candidates_token_count,
        "total_tokens": u.total_token_count,
    }


def summarize(transcript: str) -> tuple[str, dict]:
    """Generate a short summary of the conversation. Returns (summary, usage)."""
    prompt = (
        "You are summarizing a transcript of a spoken Japanese conversation or "
        "meeting. Write a concise summary in English capturing "
        "what was discussed and any decisions or action items. The transcript "
        "may contain speech-recognition errors; infer meaning where obvious and "
        "do not invent specifics.\n\nTranscript:\n" + transcript
    )

    response = _client.models.generate_content(
        model=_SUMMARY_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SummaryResult,
            # NOTE: we deliberately don't force a low temperature. Newer Gemini
            # models are tuned for their default and low temps can degrade them.
        ),
    )
    result: SummaryResult = response.parsed   # SDK parsed it into our model
    return result.summary, _usage(response)


def filter_useful_words(candidates: list[dict]) -> tuple[list[dict], dict]:
    """Given fugashi-extracted, JLPT-tagged candidate words, ask Gemini which
    are worth surfacing as study vocabulary. Returns (kept_words, usage).

    Gemini does NOT assign levels or invent words — it only judges usefulness
    and adds a gloss. Levels came from the deterministic JLPT lookup upstream.
    """
    # Send just the words; the model doesn't need readings/levels to judge.
    word_list = [c["word"] for c in candidates]

    prompt = (
        "These are dictionary-form Japanese words extracted from a meeting "
        "transcript. For each, decide whether it is worth surfacing to a "
        "language learner as study vocabulary. Mark keep=false for extremely "
        "common function words (する, ある, いる, なる, これ, etc.) and for any "
        "garbled non-words. Mark keep=true for meaningful content vocabulary. "
        "Give a short English gloss for kept words (empty string if dropped). "
        "Return a judgment for every word.\n\nWords:\n"
        + "\n".join(word_list)
    )

    response = _client.models.generate_content(
        model=_FILTER_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=FilterResult,
        ),
    )
    result: FilterResult = response.parsed

    # Build a keep-map from the model's judgments, keyed by word.
    judged = {j.word: j for j in result.judgments}

    # Merge back onto the ORIGINAL candidates so we keep reading + JLPT level
    # (which the model never saw). The model only contributed keep + gloss.
    kept = []
    for c in candidates:
        j = judged.get(c["word"])
        if j and j.keep:
            kept.append({**c, "gloss": j.gloss})
    return kept, _usage(response)