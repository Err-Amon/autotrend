import { useState } from "react";
import Home from "./pages/Home";
import Settings from "./pages/Settings";
import "./styles/index.css";

export default function App() {
  const [page, setPage] = useState("home");

  const navStyle = (p) => ({
    padding: "8px 20px",
    background: page === p ? "#1e293b" : "transparent",
    border: "none",
    color: page === p ? "#f1f5f9" : "#64748b",
    cursor: "pointer",
    borderRadius: 6,
    fontWeight: 600,
    fontSize: 14,
  });

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      <aside style={{
        width: 200, background: "#0f172a", borderRight: "1px solid #1e293b",
        display: "flex", flexDirection: "column", padding: 16, gap: 4,
      }}>
        <div style={{ fontSize: 16, fontWeight: 700, color: "#6366f1", marginBottom: 20, padding: "0 8px" }}>
          AutoTrend
        </div>
        <button style={navStyle("home")} onClick={() => setPage("home")}>Dashboard</button>
        <button style={navStyle("settings")} onClick={() => setPage("settings")}>Settings</button>
      </aside>
      <main style={{ flex: 1, padding: 32, overflowY: "auto", background: "#0f172a" }}>
        {page === "home" ? <Home /> : <Settings />}
      </main>
    </div>
  );
}
