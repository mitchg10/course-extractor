export const API_URL = process.env.NODE_ENV === 'production' 
  ? 'https://course-extractor-rior.onrender.com'
  : 'http://localhost:8000';

export const endpoints = {
    process: `${API_URL}/process`,
    status: (taskId) => `${API_URL}/status/${taskId}`,
    availableFiles: (taskId) => `${API_URL}/available-files/${taskId}`,
    download: (taskId, filename) => `${API_URL}/download/${taskId}/${filename}`
};