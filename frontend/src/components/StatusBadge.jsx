export default function StatusBadge({ status }) {
  const colors = {
    queued: "#f59e0b",
    running: "#3b82f6",
    assembled: "#8b5cf6",
    complete: "#10b981",
    failed: "#ef4444",
  };
  const color = colors[status] || "#6b7280";
  return (
    <span style={{
      backgroundColor: color,
      color: "#fff",
      padding: "2px 10px",
      borderRadius: "999px",
      fontSize: "12px",
      fontWeight: 600,
      textTransform: "uppercase",
    }}>
      {status}
    </span>
  );
}
