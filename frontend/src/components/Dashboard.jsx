import { useState, useEffect } from "react";
import NicheSelector from "./NicheSelector";
import PlatformSelector from "./PlatformSelector";
import VideoQueue from "./VideoQueue";
import LogViewer from "./LogViewer";
import { getNiches, generateVideo, getAllJobs } from "../services/api";

export default function Dashboard() {
  const [niches, setNiches] = useState([]);
  const [selectedNiche, setSelectedNiche] = useState("");
  const [selectedPlatforms, setSelectedPlatforms] = useState([]);
  const [jobs, setJobs] = useState({});
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getNiches().then((res) => {
      setNiches(res.data.niches);
      setSelectedNiche(res.data.niches[0]);
    });
    const interval = setInterval(() => {
      getAllJobs().then((res) => setJobs(res.data.jobs || {}));
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const togglePlatform = (p) =>
    setSelectedPlatforms((prev) => prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p]);

  const handleGenerate = async () => {
    if (!selectedNiche) return;
    setLoading(true);
    setLogs((l) => [...l, `Starting job: ${selectedNiche}`]);
    try {
      const res = await generateVideo(selectedNiche, selectedPlatforms, {});
      setLogs((l) => [...l, `Job queued: ${res.data.job_id}`]);
    } catch (e) {
      setLogs((l) => [...l, `Error: ${e.message}`]);
    }
    setLoading(false);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      <NicheSelector niches={niches} selected={selectedNiche} onSelect={setSelectedNiche} />
      <PlatformSelector selected={selectedPlatforms} onToggle={togglePlatform} />
      <button
        onClick={handleGenerate}
        disabled={loading}
        style={{
          background: loading ? "#334155" : "#6366f1",
          color: "#fff",
          border: "none",
          padding: "12px 24px",
          borderRadius: 8,
          fontSize: 15,
          fontWeight: 700,
          cursor: loading ? "not-allowed" : "pointer",
          alignSelf: "flex-start",
        }}
      >
        {loading ? "Queuing..." : "Generate Video"}
      </button>
      <VideoQueue jobs={jobs} />
      <LogViewer logs={logs} />
    </div>
  );
}
