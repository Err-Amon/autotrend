import { useState } from "react";

const fields = [
  { key: "GROQ_API_KEY", label: "Groq API Key" },
  { key: "PEXELS_API_KEY", label: "Pexels API Key" },
  { key: "PIXABAY_API_KEY", label: "Pixabay API Key" },
  { key: "REDDIT_CLIENT_ID", label: "Reddit Client ID" },
  { key: "REDDIT_SECRET", label: "Reddit Secret" },
  { key: "YOUTUBE_CLIENT_ID", label: "YouTube Client ID" },
  { key: "YOUTUBE_CLIENT_SECRET", label: "YouTube Client Secret" },
  { key: "FACEBOOK_ACCESS_TOKEN", label: "Facebook Access Token" },
  { key: "INSTAGRAM_ACCESS_TOKEN", label: "Instagram Access Token" },
];

export default function Settings() {
  const [values, setValues] = useState({});

  return (
    <div>
      <h2 style={{ marginBottom: 24, color: "#f8fafc" }}>Settings</h2>
      <p style={{ color: "#64748b", marginBottom: 20 }}>
        Edit your <code>.env</code> file directly to configure API keys. Reference below:
      </p>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {fields.map((f) => (
          <div key={f.key}>
            <label style={{ fontSize: 13, color: "#94a3b8", display: "block", marginBottom: 4 }}>{f.label}</label>
            <input
              type="password"
              placeholder={`${f.key}=...`}
              value={values[f.key] || ""}
              onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))}
              style={{
                width: "100%",
                padding: "8px 12px",
                background: "#1e293b",
                border: "1px solid #334155",
                borderRadius: 6,
                color: "#f1f5f9",
                fontSize: 14,
              }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
