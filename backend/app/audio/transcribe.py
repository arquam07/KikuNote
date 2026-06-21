import os
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech
from google.api_core.client_options import ClientOptions


def transcribe_file(audio_path: str, project_id: str, region: str = "us") -> str:
    """Transcribe a local audio file with Chirp 3, return the full transcript.

    Synchronous recognition: fine for clips under ~60s. For longer meeting
    audio we'll switch to batch_recognize later (Phase 1.5). Keeping it sync
    now so we can prove the pipeline end-to-end with a short test clip.
    """

    # The V2 API is regional. The api_endpoint MUST match the region used in
    # the recognizer path below, or you get a misleading "not found" error.
    client = SpeechClient(
        client_options=ClientOptions(
            api_endpoint=f"{region}-speech.googleapis.com",
            quota_project_id=project_id,
        )
    )

    # Read the audio as raw bytes. AutoDetectDecodingConfig means we don't have
    # to tell the API the sample rate / encoding — it figures out wav/mp3/flac
    # etc. itself. This is why we can feed it whatever the browser records later.
    with open(audio_path, "rb") as f:
        audio_content = f.read()

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