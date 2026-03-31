import { useState, useEffect, useCallback, useRef } from "react";
import NicheSelector from "./NicheSelector";
import PlatformSelector from "./PlatformSelector";
import VideoQueue from "./VideoQueue";
import LogViewer from "./LogViewer";
import { api } from "../services/api";

const POLL_INTERVAL = 3000;

function nowStr() {
  return new Date().toLocaleTimeString("en-US", { hour12: false });
}

export default function Dashboard() {
  const [niches, setNiches]               = useState([]);
  const [selectedNiche, setSelectedNiche] = useState("");
  const [platforms, setPlatforms]         = useState([]);
  const [jobs, setJobs]                   = useState({});
  const [logs, setLogs]                   = useState([]);
  const [loading, setLoading]             = useState(false);
  const [backendOk, setBackendOk]         = useState(null);
  const pollRef                           = useRef(null);

  const addLog = useCallback((text, type = "info") => {
    setLogs((prev) => [...prev.slice(-199), { text, type, time: nowStr() }]);
  }, []);

  // Health check + niche fetch on mount
  useEffect(() => {
    api.health()
      .then(() => {
        setBackendOk(true);
        addLog("Backend connected", "success");
        return api.getNiches();
      })
      .then((res) => {
        const list = res.data.niches || [];
        setNiches(list);
        setSelectedNiche(list[0] || "");
        addLog(`Loaded ${list.length} niches`);
      })
      .catch(() => {
        setBackendOk(false);
        addLog("Cannot connect to backend — is it running on port 8000?", "error");
      });
  }, [addLog]);

  // Poll job statuses every 3 seconds
  useEffect(() => {
    pollRef.current = setInterval(() => {
      api.getAllJobs()
        .then((res) => {
          const incoming = res.data.jobs || {};
          setJobs((prev) => {
            // Detect newly completed or failed jobs and log them
            Object.entries(incoming).forEach(([id, job]) => {
              const prev_status = prev[id]?.status;
              if (prev_status === "running" && job.status === "complete") {
                addLog(`Job #${id} completed successfully`, "success");
              }
              if (prev_status === "running" && job.status === "failed") {
                addLog(`Job #${id} failed: ${job.error || "unknown error"}`, "error");
              }
            });
            return incoming;
          });
        })
        .catch(() => {});
    }, POLL_INTERVAL);

    return () => clearInterval(pollRef.current);
  }, [addLog]);

  const togglePlatform = (id) => {
    setPlatforms((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    );
  };

  const handleGenerate = async () => {
    if (!selectedNiche) return;
    setLoading(true);
    addLog(`Queuing job: ${selectedNiche}${platforms.length ? ` → ${platforms.join(", ")}` : ""}`);

    try {
      const res = await api.generateVideo(selectedNiche, platforms, {});
      const jobId = res.data.job_id;
      addLog(`Job #${jobId} queued`, "success");
      setJobs((prev) => ({
        ...prev,
        [jobId]: { status: "queued", step: "", niche: selectedNiche },
      }));
    } catch (err) {
      addLog(`Failed to queue job: ${err.message}`, "error");
    }

    setLoading(false);
  };

  const handleDelete = async (jobId) => {
    try {
      await api.deleteJob(jobId);
      setJobs((prev) => {
        const next = { ...prev };
        delete next[jobId];
        return next;
      });
      addLog(`Removed job #${jobId}`);
    } catch (err) {
      addLog(`Could not remove job: ${err.message}`, "warn");
    }
  };

  const handleClearAll = async () => {
    try {
      await api.clearJobs();
      setJobs({});
      addLog("All jobs cleared");
    } catch (err) {
      addLog(`Clear failed: ${err.message}`, "warn");
    }
  };

  const jobCount = Object.keys(jobs).length;
  const runningCount = Object.values(jobs).filter((j) => j.status === "running").length;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>

      {/* Backend status banner */}
      {backendOk === false && (
        <div style={{
          padding: "10px 16px",
          background: "rgba(239,68,68,0.12)",
          border: "1px solid #ef4444",
          borderRadius: 8,
          color: "#ef4444",
          fontSize: 13,
        }}>
          ⚠ Backend not reachable. Run: <code style={{ background: "#1e293b", padding: "1px 6px", borderRadius: 4 }}>cd backend && uvicorn main:app --reload --port 8000</code>
        </div>
      )}

      {/* Niche selector */}
      <NicheSelector
        niches={niches}
        selected={selectedNiche}
        onSelect={setSelectedNiche}
      />

      {/* Platform selector */}
      <PlatformSelector
        selected={platforms}
        onToggle={togglePlatform}
      />

      {/* Generate button */}
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <button
          onClick={handleGenerate}
          disabled={loading || !selectedNiche || backendOk === false}
          style={{
            padding: "10px 28px",
            background: loading ? "#334155" : "#6366f1",
            color: "#fff",
            borderRadius: 8,
            fontWeight: 700,
            fontSize: 14,
            letterSpacing: "0.02em",
          }}
        >
          {loading ? "Queuing..." : "⚡ Generate Video"}
        </button>

        {runningCount > 0 && (
          <span style={{ color: "#3b82f6", fontSize: 13 }}>
            {runningCount} job{runningCount > 1 ? "s" : ""} running...
          </span>
        )}
      </div>

      {/* Queue section */}
      <section>
        <div style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 12,
        }}>
          <h3 style={{ fontSize: 13, fontWeight: 700, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.08em" }}>
            Video Queue
            {jobCount > 0 && (
              <span style={{ marginLeft: 8, color: "#475569", fontWeight: 400, textTransform: "none" }}>
                ({jobCount} job{jobCount !== 1 ? "s" : ""})
              </span>
            )}
          </h3>
          {jobCount > 0 && (
            <button
              onClick={handleClearAll}
              style={{
                background: "transparent",
                color: "#475569",
                fontSize: 12,
                padding: "3px 8px",
                borderRadius: 4,
                border: "1px solid #334155",
              }}
            >
              Clear All
            </button>
          )}
        </div>
        <VideoQueue jobs={jobs} onDelete={handleDelete} />
      </section>

      {/* Log viewer */}
      <section>
        <h3 style={{
          fontSize: 13,
          fontWeight: 700,
          color: "#64748b",
          textTransform: "uppercase",
          letterSpacing: "0.08em",
          marginBottom: 8,
        }}>
          Activity Log
        </h3>
        <LogViewer logs={logs} />
      </section>
    </div>
  );
}