const NICHE_ICONS = {
  "Islamic History": "",
  "Technology":      "",
  "Motivation":      "",
  "Animals":         "",
  "Finance":         "",
  "Space & Science": "",
};

export default function NicheSelector({ niches = [], selected, onSelect }) {
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
        Select Niche
      </label>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        {niches.map((niche) => {
          const isSelected = selected === niche;
          return (
            <button
              key={niche}
              onClick={() => onSelect(niche)}
              style={{
                padding: "7px 14px",
                borderRadius: 6,
                border: `2px solid ${isSelected ? "#6366f1" : "#334155"}`,
                background: isSelected ? "#6366f1" : "transparent",
                color: isSelected ? "#fff" : "#94a3b8",
                fontWeight: 600,
                fontSize: 13,
                display: "flex",
                alignItems: "center",
                gap: 6,
                transition: "all 0.15s",
              }}
            >
              <span>{NICHE_ICONS[niche] || ""}</span>
              {niche}
            </button>
          );
        })}
      </div>
    </div>
  );
}