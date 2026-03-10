import axios from "axios";

const BASE_URL = "http://localhost:8000/api";
const api = axios.create({ baseURL: BASE_URL, timeout: 30000 });

export const getNiches = () => api.get("/niches");
export const generateVideo = (niche, platforms, uploadConfig) =>
  api.post("/generate", { niche, platforms, upload_config: uploadConfig });
export const queueVideos = (jobs) => api.post("/queue", { jobs });
export const getJobStatus = (jobId) => api.get(`/status/${jobId}`);
export const getAllJobs = () => api.get("/jobs");
