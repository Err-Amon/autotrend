export default function NicheSelector({ niches, selected, onSelect }) {
  return (
    <div>
      <label style={{ fontWeight: 600, display: "block", marginBottom: 8 }}>Select Niche</label>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        {niches.map((n) => (
          <button
            key={n}
            onClick={() => onSelect(n)}
            style={{
              padding: "6px 16px",
              borderRadius: 6,
              border: "2px solid",
              borderColor: selected === n ? "#6366f1" : "#334155",
              background: selected === n ? "#6366f1" : "transparent",
              color: selected === n ? "#fff" : "#94a3b8",
              cursor: "pointer",
              fontWeight: 500,
            }}
          >
            {n}
          </button>
        ))}
      </div>
    </div>
  );
}
