const STATUS_STYLES = {
  queued:    { bg: "#f59e0b", label: "Queued" },
  running:   { bg: "#3b82f6", label: "Running" },
  assembled: { bg: "#8b5cf6", label: "Assembled" },
  complete:  { bg: "#10b981", label: "Complete" },
  failed:    { bg: "#ef4444", label: "Failed" },
};

export default function StatusBadge({ status }) {
  const style = STATUS_STYLES[status] || { bg: "#475569", label: status };

  return (
    <span style={{
      display: "inline-block",
      padding: "2px 10px",
      borderRadius: "999px",
      background: style.bg,
      color: "#fff",
      fontSize: "11px",
      fontWeight: 700,
      letterSpacing: "0.04em",
      textTransform: "uppercase",
      whiteSpace: "nowrap",
    }}>
      {style.label}
    </span>
  );
}