import { useState } from "react";
import { useRecorder } from "./hooks/useRecorder";
import { processAudio, type ProcessResult } from "./api";
import Results from "./components/Results";

export default function App() {
  const recorder = useRecorder();

  // High-level UI state. `loading` covers the upload + transcription + LLM
  // round-trip, which takes several seconds — the user must see it's working.
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ProcessResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Start recording. Recorder-level errors (e.g. denied mic) surface via
  // recorder.error, which we display below.
  async function handleStart() {
    setError(null);
    setResult(null);
    try {
      await recorder.start();
    } catch {
      // useRecorder already set a readable message in recorder.error.
    }
  }

  // Stop recording, then upload the blob and render the response.
  async function handleStop() {
    let recording;
    try {
      recording = await recorder.stop();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not stop recording.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await processAudio(recording.blob, recording.filename);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  // The record/stop control is a single toggle. While a request is in flight
  // we disable it so the user can't fire a second recording mid-upload.
  const isRecording = recorder.recording;

  return (
    <main className="app">
      <header className="header">
        <h1>KikuNote 聞くノート</h1>
        <p className="tagline">
          Record a Japanese conversation, get a transcript, summary, and
          leveled vocabulary list.
        </p>
      </header>

      <div className="controls">
        <button
          className={isRecording ? "btn btn-stop" : "btn btn-record"}
          onClick={isRecording ? handleStop : handleStart}
          disabled={loading}
        >
          {isRecording ? "■ Stop & process" : "● Record"}
        </button>

        {/* Clear visual indication that recording is in progress. */}
        {isRecording && (
          <div className="recording-indicator">
            <span className="dot" /> Recording…
          </div>
        )}
      </div>

      {/* Recorder errors (mic permission, no device) and request errors. */}
      {(recorder.error || error) && (
        <div className="error" role="alert">
          {recorder.error ?? error}
        </div>
      )}

      {/* Loading state for the multi-second backend round-trip. */}
      {loading && (
        <div className="loading">
          <span className="spinner" />
          Transcribing and analyzing… this can take several seconds.
        </div>
      )}

      {result && !loading && <Results result={result} />}
    </main>
  );
}
