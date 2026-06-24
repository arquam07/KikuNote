import { useCallback, useRef, useState } from "react";

// The recorded result: the audio blob plus a filename whose extension matches
// the format the browser actually produced. The backend uses that extension.
export interface Recording {
  blob: Blob;
  filename: string;
}

export interface UseRecorder {
  recording: boolean; // true while actively capturing the mic
  error: string | null; // mic-permission / recording errors, human-readable
  start: () => Promise<void>;
  stop: () => Promise<Recording>; // resolves with the finished recording
}

/**
 * Pick a container/codec the browser supports. Chrome/Firefox give us WebM;
 * Safari only does mp4. We return the mime type AND a matching file extension
 * so the upload's filename tells the backend what it's dealing with.
 */
function pickMimeType(): { mimeType: string; ext: string } {
  const candidates: { mimeType: string; ext: string }[] = [
    { mimeType: "audio/webm", ext: "webm" },
    { mimeType: "audio/mp4", ext: "mp4" },
    { mimeType: "audio/ogg", ext: "ogg" },
  ];
  for (const c of candidates) {
    if (MediaRecorder.isTypeSupported(c.mimeType)) return c;
  }
  // Last resort: let the browser choose. We still send a generic name.
  return { mimeType: "", ext: "webm" };
}

/**
 * Thin typed wrapper around the browser MediaRecorder API.
 *
 * Usage:
 *   const rec = useRecorder();
 *   await rec.start();              // begins capture (asks mic permission)
 *   const result = await rec.stop(); // ends capture, returns { blob, filename }
 */
export function useRecorder(): UseRecorder {
  const [recording, setRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Refs hold values that must survive re-renders without triggering them:
  // the active recorder, the mic stream (so we can stop its tracks), the
  // collected data chunks, and the extension chosen at start().
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const extRef = useRef<string>("webm");

  const start = useCallback(async () => {
    setError(null);
    try {
      // Prompt for mic access. Throws if the user denies permission.
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const { mimeType, ext } = pickMimeType();
      extRef.current = ext;

      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);

      chunksRef.current = [];
      recorder.ondataavailable = (e: BlobEvent) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorderRef.current = recorder;
      recorder.start();
      setRecording(true);
    } catch (err) {
      // Most commonly a denied mic permission. Give a readable message.
      const name = err instanceof DOMException ? err.name : "";
      if (name === "NotAllowedError" || name === "SecurityError") {
        setError("Microphone permission was denied. Please allow mic access and try again.");
      } else if (name === "NotFoundError") {
        setError("No microphone was found on this device.");
      } else {
        setError(err instanceof Error ? err.message : "Could not start recording.");
      }
      throw err;
    }
  }, []);

  const stop = useCallback((): Promise<Recording> => {
    return new Promise((resolve, reject) => {
      const recorder = recorderRef.current;
      if (!recorder) {
        reject(new Error("Not currently recording."));
        return;
      }

      // onstop fires after the final chunk has been delivered, so we assemble
      // the blob here rather than risk missing trailing data.
      recorder.onstop = () => {
        // Release the mic so the browser's "recording" indicator turns off.
        streamRef.current?.getTracks().forEach((t) => t.stop());
        streamRef.current = null;

        const type = recorder.mimeType || "audio/webm";
        const blob = new Blob(chunksRef.current, { type });
        const filename = `recording.${extRef.current}`;

        recorderRef.current = null;
        setRecording(false);
        resolve({ blob, filename });
      };

      recorder.stop();
    });
  }, []);

  return { recording, error, start, stop };
}
