import StatusBadge from "./StatusBadge";

export default function VideoQueue({ jobs }) {
  const entries = Object.entries(jobs);
  return (
    <div>
      <h3 style={{ marginBottom: 12 }}>Video Queue</h3>
      {entries.length === 0 ? (
        <p style={{ color: "#475569" }}>No jobs yet.</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", color: "#64748b", fontSize: 13 }}>
              <th style={{ padding: "6px 0" }}>Job ID</th>
              <th>Status</th>
              <th>Step</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([id, job]) => (
              <tr key={id} style={{ borderTop: "1px solid #1e293b" }}>
                <td style={{ padding: "8px 0", fontFamily: "monospace", fontSize: 13 }}>{id}</td>
                <td><StatusBadge status={job.status} /></td>
                <td style={{ color: "#94a3b8", fontSize: 13 }}>{job.step || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
