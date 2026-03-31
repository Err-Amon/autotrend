import StatusBadge from "./StatusBadge";

const STEP_LABELS = {
  collecting_trends:   "Collecting trends",
  filtering_trends:    "Filtering trends",
  generating_script:   "Generating script",
  generating_voice:    "Generating voice",
  fetching_clips:      "Fetching clips",
  generating_subtitles:"Generating subtitles",
  assembling_video:    "Assembling video",
  uploading:           "Uploading",
  complete:            "Done",
};

export default function VideoQueue({ jobs = {}, onDelete }) {
  const entries = Object.entries(jobs);

  if (entries.length === 0) {
    return (
      <div style={{
        padding: "32px 0",
        textAlign: "center",
        color: "#334155",
        fontSize: 13,
      }}>
        No jobs yet. Generate a video to get started.
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {entries.map(([id, job]) => (
        <div key={id} style={{
          background: "#1e293b",
          border: "1px solid #273549",
          borderRadius: 8,
          padding: "12px 16px",
          display: "flex",
          alignItems: "center",
          gap: 12,
        }}>
          {/* Job ID */}
          <span style={{
            fontFamily: "monospace",
            fontSize: 12,
            color: "#475569",
            minWidth: 70,
          }}>
            #{id}
          </span>

          {/* Niche */}
          <span style={{
            fontSize: 13,
            color: "#cbd5e1",
            fontWeight: 600,
            minWidth: 120,
          }}>
            {job.niche || "—"}
          </span>

          {/* Status badge */}
          <StatusBadge status={job.status} />

          {/* Current step */}
          <span style={{
            fontSize: 12,
            color: "#64748b",
            flex: 1,
          }}>
            {job.status === "running"
              ? (STEP_LABELS[job.step] || job.step || "Processing...")
              : job.status === "failed"
              ? (job.error || "Failed")
              : job.status === "complete"
              ? (job.video_path ? `✓ ${job.video_path.split(/[\\/]/).pop()}` : "Complete")
              : "Queued"}
          </span>

          {/* Progress indicator for running jobs */}
          {job.status === "running" && (
            <span style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              background: "#3b82f6",
              animation: "pulse 1.2s ease-in-out infinite",
              flexShrink: 0,
            }} />
          )}

          {/* Delete button */}
          {(job.status === "complete" || job.status === "failed") && onDelete && (
            <button
              onClick={() => onDelete(id)}
              title="Remove from list"
              style={{
                background: "transparent",
                color: "#475569",
                padding: "2px 6px",
                borderRadius: 4,
                fontSize: 14,
                lineHeight: 1,
                flexShrink: 0,
              }}
            >
              ✕
            </button>
          )}
        </div>
      ))}

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
      `}</style>
    </div>
  );
}