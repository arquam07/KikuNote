import os
import subprocess
import tempfile
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech
from google.api_core.client_options import ClientOptions


def _convert_to_wav(src_path: str) -> str:
    """Convert any audio file to 16kHz mono PCM WAV via ffmpeg, return new path.

    Browsers' MediaRecorder produces WebM/Opus (Chrome/Firefox) or mp4/AAC
    (Safari). Chirp accepts those nominally but returns empty results on some
    of them, so we normalize everything to a plain WAV first — the format Chirp
    handles most reliably. Caller is responsible for deleting the returned file.
    """
    # Write to a fresh temp path; we only need ffmpeg to own the output file.
    fd, wav_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)  # ffmpeg writes the file itself; we just need the name.

    # -y: overwrite the (empty) temp file. -ar 16000 mono PCM s16le is the
    # canonical STT input format. -i must come before output options.
    cmd = [
        "ffmpeg", "-y",
        "-i", src_path,
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        wav_path,
    ]
    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError:
        os.remove(wav_path)
        raise RuntimeError(
            "ffmpeg not found on PATH. Install ffmpeg (it is now a backend "
            "dependency) — see the README."
        )
    except subprocess.CalledProcessError as e:
        os.remove(wav_path)
        msg = e.stderr.decode("utf-8", "replace") if e.stderr else ""
        raise RuntimeError(f"ffmpeg failed to convert audio: {msg}")

    return wav_path


def transcribe_file(audio_path: str, project_id: str, region: str = "us") -> str:
    """Transcribe a local audio file with Chirp 3, return the full transcript.

    Synchronous recognition: fine for clips under ~60s. For longer meeting
    audio we'll switch to batch_recognize later (Phase 1.5). Keeping it sync
    now so we can prove the pipeline end-to-end with a short test clip.
    """

    # Normalize whatever was uploaded (browser WebM/mp4, mp3, etc.) to WAV
    # before transcription. Delete the converted file once we've read it.
    wav_path = _convert_to_wav(audio_path)

    # The V2 API is regional. The api_endpoint MUST match the region used in
    # the recognizer path below, or you get a misleading "not found" error.
    client = SpeechClient(
        client_options=ClientOptions(
            api_endpoint=f"{region}-speech.googleapis.com",
            quota_project_id=project_id,
        )
    )

    # Read the converted WAV as raw bytes. AutoDetectDecodingConfig still works
    # fine on it and keeps the call identical whether or not we convert.
    try:
        with open(wav_path, "rb") as f:
            audio_content = f.read()
    finally:
        os.remove(wav_path)  # don't leak the converted temp file

    config = cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        language_codes=["ja-JP"],   # Japanese. Use ["auto"] for auto-detect.
        model="chirp_3",
    )

    # recognizers/_  is the implicit recognizer — we don't have to pre-create
    # a named recognizer resource for sync requests. The "_" is literal.
    request = cloud_speech.RecognizeRequest(
        recognizer=f"projects/{project_id}/locations/{region}/recognizers/_",
        config=config,
        content=audio_content,
    )

    response = client.recognize(request=request)

    # The response is a list of result segments, each with ranked alternatives.
    # alternatives[0] is the best guess. We stitch the segments into one string.
    transcript_parts = [
        result.alternatives[0].transcript
        for result in response.results
        if result.alternatives
    ]
    return "".join(transcript_parts)  # Japanese has no spaces between words.