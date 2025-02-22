const BASE_URL =
  import.meta.env.ENVIRONMENT === "production"
    ? "/api"
    : "http://localhost:8000/api";

export const endpoints = {
  process: `${BASE_URL}/process`,
  status: (taskId) => `${BASE_URL}/status/${taskId}`,
  availableFiles: (taskId) => `${BASE_URL}/available-files/${taskId}`,
  download: (taskId, filename) => `${BASE_URL}/download/${taskId}/${filename}`,
  health: `${BASE_URL}/health`,
  frontendLogs: `${BASE_URL}/frontend-logs`,
};
