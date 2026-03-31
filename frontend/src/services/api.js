import axios from "axios";

const client = axios.create({
  baseURL: "http://localhost:8000/api",
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

// Intercept errors globally so components only handle business logic
client.interceptors.response.use(
  (res) => res,
  (err) => {
    const message =
      err.response?.data?.detail ||
      err.response?.data?.message ||
      err.message ||
      "Unknown error";
    return Promise.reject(new Error(message));
  }
);

export const api = {
  health: () =>
    client.get("/health"),

  getNiches: () =>
    client.get("/niches"),

  generateVideo: (niche, platforms = [], uploadConfig = {}) =>
    client.post("/generate", {
      niche,
      platforms,
      upload_config: uploadConfig,
    }),

  queueVideos: (jobs) =>
    client.post("/queue", { jobs }),

  getJobStatus: (jobId) =>
    client.get(`/status/${jobId}`),

  getAllJobs: () =>
    client.get("/jobs"),

  deleteJob: (jobId) =>
    client.delete(`/jobs/${jobId}`),

  clearJobs: () =>
    client.delete("/jobs"),
};