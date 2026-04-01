import { useState } from "react";

const SECTIONS = [
  {
    title: "LLM — Google AI Studio",
    fields: [
      {
        key: "GOOGLE_AI_STUDIO_API_KEY",
        label: "Google AI Studio API Key",
        type: "password",
        hint: "Get free key from aistudio.google.com → API Keys",
        required: true,
      },
    ],
  },
  {
    title: "Stock Video",
    fields: [
      {
        key: "PEXELS_API_KEY",
        label: "Pexels API Key",
        type: "password",
        hint: "pexels.com/api → sign in → your key is on the dashboard",
        required: true,
      },
      {
        key: "PIXABAY_API_KEY",
        label: "Pixabay API Key",
        type: "password",
        hint: "pixabay.com/api/docs → sign in → key shown at top (optional)",
        required: false,
      },
    ],
  },
  {
    title: "YouTube Upload",
    fields: [
      {
        key: "YOUTUBE_CLIENT_ID",
        label: "YouTube Client ID",
        type: "text",
        hint: "console.cloud.google.com → YouTube Data API v3 → OAuth 2.0 Desktop App",
        required: false,
      },
      {
        key: "YOUTUBE_CLIENT_SECRET",
        label: "YouTube Client Secret",
        type: "password",
        hint: "From the same OAuth 2.0 credentials screen",
        required: false,
      },
    ],
  },
  {
    title: "Facebook Upload",
    fields: [
      {
        key: "FACEBOOK_ACCESS_TOKEN",
        label: "Facebook Access Token",
        type: "password",
        hint: "developers.facebook.com → Graph API Explorer → Page Access Token",
        required: false,
      },
      {
        key: "FACEBOOK_PAGE_ID",
        label: "Facebook Page ID",
        type: "text",
        hint: "Your Facebook Page → Settings → About → Page ID",
        required: false,
      },
    ],
  },
  {
    title: "Instagram Upload",
    fields: [
      {
        key: "INSTAGRAM_ACCESS_TOKEN",
        label: "Instagram Access Token",
        type: "password",
        hint: "Same Facebook app → Instagram Graph API → token with instagram_content_publish",
        required: false,
      },
      {
        key: "INSTAGRAM_USER_ID",
        label: "Instagram User ID",
        type: "text",
        hint: "Call GET /me?fields=id with your token to get this value",
        required: false,
      },
    ],
  },
  {
    title: "Piper TTS (Voice)",
    fields: [
      {
        key: "PIPER_EXECUTABLE",
        label: "Piper Executable Path",
        type: "text",
        hint: "Name or full path of piper binary. Default: piper (if it's in PATH)",
        required: true,
      },
      {
        key: "PIPER_MODEL_PATH",
        label: "Piper Model Path (.onnx)",
        type: "text",
        hint: "Path to .onnx model file. Download from huggingface.co/rhasspy/piper-voices",
        required: true,
      },
    ],
  },
];

function Field({ label, fieldKey, type, hint, required }) {
  const [show, setShow] = useState(false);
  const isPassword = type === "password";

  return (
    <div style={{ marginBottom: 16 }}>
      <label style={{
        display: "flex",
        alignItems: "center",
        gap: 6,
        fontSize: 13,
        fontWeight: 600,
        color: "#cbd5e1",
        marginBottom: 5,
      }}>
        {label}
        {required && (
          <span style={{ color: "#ef4444", fontSize: 11 }}>required</span>
        )}
      </label>

      <div style={{ position: "relative" }}>
        <input
          type={isPassword && !show ? "password" : "text"}
          placeholder={`${fieldKey}=...`}
          style={{
            width: "100%",
            padding: "8px 36px 8px 12px",
            background: "#1e293b",
            borderRadius: 6,
            color: "#f1f5f9",
            fontSize: 13,
          }}
          readOnly
        />
        {isPassword && (
          <button
            onClick={() => setShow((s) => !s)}
            style={{
              position: "absolute",
              right: 8,
              top: "50%",
              transform: "translateY(-50%)",
              background: "transparent",
              color: "#475569",
              fontSize: 13,
              padding: "0 4px",
            }}
          >
            {show ? "" : ""}
          </button>
        )}
      </div>

      <p style={{ color: "#475569", fontSize: 12, marginTop: 4 }}>
        {hint}
      </p>
    </div>
  );
}

export default function Settings() {
  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 20, fontWeight: 700, color: "#f1f5f9" }}>
          Settings
        </h2>
        <p style={{ color: "#64748b", fontSize: 13, marginTop: 4 }}>
          All credentials are stored in your <code style={{
            background: "#1e293b",
            padding: "1px 6px",
            borderRadius: 4,
            fontSize: 12,
          }}>.env</code> file in the project root.
          Edit that file directly — changes take effect when you restart the backend.
        </p>
      </div>

      <div style={{
        background: "rgba(99,102,241,0.08)",
        border: "1px solid rgba(99,102,241,0.25)",
        borderRadius: 8,
        padding: "10px 14px",
        marginBottom: 24,
        fontSize: 13,
        color: "#a5b4fc",
      }}>
        ℹ Minimum required to run the pipeline: <strong>GOOGLE_AI_STUDIO_API_KEY</strong> and <strong>PEXELS_API_KEY</strong>.
        All upload keys are optional — you can generate videos without uploading.
      </div>

      {SECTIONS.map((section) => (
        <div key={section.title} style={{ marginBottom: 28 }}>
          <h3 style={{
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            color: "#475569",
            marginBottom: 14,
            paddingBottom: 8,
            borderBottom: "1px solid #1e293b",
          }}>
            {section.title}
          </h3>
          {section.fields.map((f) => (
            <Field
              key={f.key}
              fieldKey={f.key}
              label={f.label}
              type={f.type}
              hint={f.hint}
              required={f.required}
            />
          ))}
        </div>
      ))}
    </div>
  );
}