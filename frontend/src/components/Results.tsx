import type { ProcessResult } from "../api";

// Renders the three output sections once /process returns:
// transcript, summary, and the vocabulary table.

export default function Results({ result }: { result: ProcessResult }) {
  return (
    <div className="results">
      <section className="card">
        <h2>Transcript</h2>
        {/* Japanese transcript; preserve it as plain text. */}
        <p className="transcript">{result.transcript || "(empty transcript)"}</p>
      </section>

      <section className="card">
        <h2>Summary</h2>
        <p className="summary">{result.summary || "(no summary)"}</p>
      </section>

      <section className="card">
        <h2>Vocabulary ({result.vocab.length})</h2>
        {result.vocab.length === 0 ? (
          <p className="muted">No vocabulary was extracted.</p>
        ) : (
          <table className="vocab-table">
            <thead>
              <tr>
                <th>Word</th>
                <th>Reading</th>
                <th>JLPT</th>
                <th>Meaning</th>
              </tr>
            </thead>
            <tbody>
              {result.vocab.map((v, i) => (
                <tr key={`${v.word}-${i}`}>
                  <td className="word" lang="ja">{v.word}</td>
                  <td className="reading" lang="ja">{v.reading}</td>
                  <td>
                    <span className={`level level-${v.level.toLowerCase()}`}>
                      {v.level}
                    </span>
                  </td>
                  <td>{v.gloss}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
