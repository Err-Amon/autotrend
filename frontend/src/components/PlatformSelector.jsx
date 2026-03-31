const PLATFORMS = [
  { id: "youtube",   label: "YouTube Shorts",   icon: "▶" },
  { id: "instagram", label: "Instagram Reels",  icon: "📸" },
  { id: "facebook",  label: "Facebook Reels",   icon: "👍" },
];

export default function PlatformSelector({ selected = [], onToggle }) {
  return (
    <div>
      <label style={{
        display: "block",
        fontSize: 11,
        fontWeight: 700,
        letterSpacing: "0.08em",
        textTransform: "uppercase",
        color: "#64748b",
        marginBottom: 10,
      }}>
        Upload Platforms
        <span style={{ color: "#475569", fontWeight: 400, textTransform: "none", marginLeft: 6 }}>
          (optional — leave empty to only generate video)
        </span>
      </label>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        {PLATFORMS.map(({ id, label, icon }) => {
          const isSelected = selected.includes(id);
          return (
            <button
              key={id}
              onClick={() => onToggle(id)}
              style={{
                padding: "7px 14px",
                borderRadius: 6,
                border: `2px solid ${isSelected ? "#10b981" : "#334155"}`,
                background: isSelected ? "rgba(16,185,129,0.12)" : "transparent",
                color: isSelected ? "#10b981" : "#94a3b8",
                fontWeight: 600,
                fontSize: 13,
                display: "flex",
                alignItems: "center",
                gap: 6,
                transition: "all 0.15s",
              }}
            >
              <span>{icon}</span>
              {label}
            </button>
          );
        })}
      </div>
    </div>
  );
}