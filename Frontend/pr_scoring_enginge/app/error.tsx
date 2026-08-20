"use client";

export default function GlobalError({ error, reset }: { error: Error; reset: () => void }) {
  // Keep the error available for future telemetry without exposing internals in the UI.
  void error;
  return (
    <div role="alert">
      <h2>Something went wrong.</h2>
      <button onClick={reset} type="button">Try again</button>
    </div>
  );
}
