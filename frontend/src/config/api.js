const BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:8000'
  : 'https://course-extractor-rior.onrender.com';

export const endpoints = {
    process: `${BASE_URL}/process`,
    status: (taskId) => `${BASE_URL}/status/${taskId}`,
    availableFiles: (taskId) => `${BASE_URL}/available-files/${taskId}`,
    download: (taskId, filename) => `${BASE_URL}/download/${taskId}/${filename}`,
    health: `${BASE_URL}/health`
};