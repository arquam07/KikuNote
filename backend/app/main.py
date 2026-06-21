import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.pipeline import process_audio

load_dotenv()

PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
REGION = os.getenv("STT_REGION", "asia-northeast1")

app = FastAPI(title="KikuNote API")

# CORS: the React dev server (Vite, usually :5173) is a different origin
# from this API (:8000). Browsers block cross-origin requests unless the
# server explicitly allows them. For local dev we allow the Vite origin.
# Phase 1 only — tighten this before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    # Trivial endpoint to confirm the server is up before debugging uploads.
    return {"status": "ok"}


@app.post("/process")
async def process(audio: UploadFile = File(...)):
    # The upload is a stream of bytes, but transcribe_file reads from a path.
    # So we persist the bytes to a temp file, process it, then clean up.
    # We keep the original suffix so AutoDetectDecodingConfig sees e.g. .mp3.
    suffix = os.path.splitext(audio.filename or "")[1] or ".bin"

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await audio.read())
            tmp_path = tmp.name
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save upload: {e}")

    try:
        result = process_audio(tmp_path, PROJECT_ID, REGION)
        return result
    except Exception as e:
        # Surface the real error during dev so you can debug.
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.remove(tmp_path)  # don't leak temp files