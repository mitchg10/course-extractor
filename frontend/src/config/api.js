const BASE_URL = import.meta.env.ENVIRONMENT === 'production'
  ? '/api' 
  : `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api`;  // Development

export const endpoints = {
    process: `${BASE_URL}/process`,
    status: (taskId) => `${BASE_URL}/status/${taskId}`,
    availableFiles: (taskId) => `${BASE_URL}/available-files/${taskId}`,
    download: (taskId, filename) => `${BASE_URL}/download/${taskId}/${filename}`,
    health: `${BASE_URL}/health`,
    frontendLogs: `${BASE_URL}/frontend-logs`
};