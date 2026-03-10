const PLATFORMS = ["youtube", "instagram", "facebook"];

export default function PlatformSelector({ selected, onToggle }) {
  return (
    <div>
      <label style={{ fontWeight: 600, display: "block", marginBottom: 8 }}>Upload Platforms</label>
      <div style={{ display: "flex", gap: 8 }}>
        {PLATFORMS.map((p) => (
          <button
            key={p}
            onClick={() => onToggle(p)}
            style={{
              padding: "6px 16px",
              borderRadius: 6,
              border: "2px solid",
              borderColor: selected.includes(p) ? "#10b981" : "#334155",
              background: selected.includes(p) ? "#10b981" : "transparent",
              color: selected.includes(p) ? "#fff" : "#94a3b8",
              cursor: "pointer",
              fontWeight: 500,
              textTransform: "capitalize",
            }}
          >
            {p}
          </button>
        ))}
      </div>
    </div>
  );
}
