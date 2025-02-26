// const BASE_URL =
//   import.meta.env.NODE_ENV === "production"
//     ? "https://course-extractor-rior.onrender.com/api"
//     : "http://localhost:8000/api";

// export const endpoints = {
//   process: `${BASE_URL}/process`,
//   status: (taskId) => `${BASE_URL}/status/${taskId}`,
//   availableFiles: (taskId) => `${BASE_URL}/available-files/${taskId}`,
//   download: (taskId, filename) => `${BASE_URL}/download/${taskId}/${filename}`,
//   health: `${BASE_URL}/health`,
//   frontendLogs: `${BASE_URL}/frontend-logs`,
// };

const isProd = process.env.NODE_ENV === "production";
console.log(
  `API initializing in ${isProd ? "production" : "development"} mode`
);

const BASE_URL = isProd
  ? "https://course-extractor-rior.onrender.com/api"
  : "http://localhost:8000/api";

export const endpoints = {
  process: `${BASE_URL}/process`,
  status: (taskId) => `${BASE_URL}/status/${taskId}`,
  availableFiles: (taskId) => `${BASE_URL}/available-files/${taskId}`,
  download: (taskId, filename) => `${BASE_URL}/download/${taskId}/${filename}`,
  health: `${BASE_URL}/health`,
  frontendLogs: `${BASE_URL}/frontend-logs`,
};

// Log the configured endpoints for debugging
console.log("API Endpoints configured:", {
  baseUrl: BASE_URL,
  frontendLogs: endpoints.frontendLogs,
});
