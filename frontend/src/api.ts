// Types and the single API call for KikuNote.
//
// These types mirror EXACTLY what the backend's POST /process returns
// (see backend/app/pipeline.py and backend/app/llm/analyze.py).

/** One vocabulary word the backend decided was worth surfacing. */
export interface VocabWord {
  word: string; // dictionary / written form, e.g. "会議"
  reading: string; // katakana reading, e.g. "カイギ"
  level: string; // JLPT level "N5".."N1", or "unknown"
  gloss: string; // short English meaning
}

/** The full JSON body returned by POST /process. */
export interface ProcessResult {
  transcript: string;
  summary: string;
  vocab: VocabWord[];
  // The backend also returns a `usage` object (token counts) which we don't
  // render. We leave it out of the type since the UI never touches it.
}

/**
 * Send recorded audio to the backend for transcription + analysis.
 *
 * The request goes to the relative path "/process"; in development Vite's
 * proxy (see vite.config.ts) forwards it to the FastAPI server on :8000.
 *
 * @param blob     the recorded audio from MediaRecorder
 * @param filename a name WITH the correct extension (e.g. "recording.webm"),
 *                 because the backend reads the extension to detect the format.
 */
export async function processAudio(
  blob: Blob,
  filename: string
): Promise<ProcessResult> {
  // FastAPI's endpoint signature is `audio: UploadFile = File(...)`, so the
  // form field name MUST be exactly "audio".
  const form = new FormData();
  form.append("audio", blob, filename);

  const response = await fetch("/process", {
    method: "POST",
    body: form,
    // Note: do NOT set Content-Type manually. The browser sets the correct
    // multipart/form-data boundary header automatically for FormData.
  });

  if (!response.ok) {
    // FastAPI errors come back as { "detail": "..." }; surface it if present.
    let detail = `Request failed (HTTP ${response.status})`;
    try {
      const body = await response.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // Response wasn't JSON; keep the generic message.
    }
    throw new Error(detail);
  }

  return (await response.json()) as ProcessResult;
}
