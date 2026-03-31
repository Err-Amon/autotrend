import { useEffect, useRef } from "react";

export default function LogViewer({ logs = [] }) {
  const bottomRef = useRef(null);

  // Auto-scroll to latest log entry
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  return (
    <div style={{
      background: "#0a1628",
      border: "1px solid #1e293b",
      borderRadius: 8,
      padding: "10px 12px",
      height: 180,
      overflowY: "auto",
      fontFamily: "'Courier New', Courier, monospace",
      fontSize: 12,
      color: "#94a3b8",
    }}>
      {logs.length === 0 ? (
        <span style={{ color: "#334155" }}>Waiting for pipeline to start...</span>
      ) : (
        logs.map((entry, i) => (
          <div key={i} style={{
            marginBottom: 3,
            color: entry.type === "error" ? "#ef4444"
                 : entry.type === "warn"  ? "#f59e0b"
                 : entry.type === "success" ? "#10b981"
                 : "#94a3b8",
          }}>
            <span style={{ color: "#334155", marginRight: 8 }}>
              {entry.time}
            </span>
            {entry.text}
          </div>
        ))
      )}
      <div ref={bottomRef} />
    </div>
  );
}