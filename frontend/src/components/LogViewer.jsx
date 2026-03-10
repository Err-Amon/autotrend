export default function LogViewer({ logs }) {
  return (
    <div style={{
      background: "#0f172a",
      color: "#94a3b8",
      fontFamily: "monospace",
      fontSize: "13px",
      padding: "12px",
      borderRadius: "8px",
      height: "160px",
      overflowY: "auto",
    }}>
      {logs.length === 0 ? (
        <span style={{ color: "#475569" }}>No logs yet.</span>
      ) : (
        logs.map((log, i) => <div key={i}>&gt; {log}</div>)
      )}
    </div>
  );
}
