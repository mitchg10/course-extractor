// export const API_URL = process.env.NODE_ENV === 'production' 
//   ? 'https://course-extractor-rior.onrender.com'
//   : 'http://localhost:8000';

// export const endpoints = {
//     process: `${API_URL}/process`,
//     status: (taskId) => `${API_URL}/status/${taskId}`,
//     availableFiles: (taskId) => `${API_URL}/available-files/${taskId}`,
//     download: (taskId, filename) => `${API_URL}/download/${taskId}/${filename}`
// };

const BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:8000'
  : '';  // Use relative paths in production

export const endpoints = {
    process: `${BASE_URL}/process`,
    status: (taskId) => `${BASE_URL}/status/${taskId}`,
    availableFiles: (taskId) => `${BASE_URL}/available-files/${taskId}`,
    download: (taskId, filename) => `${BASE_URL}/download/${taskId}/${filename}`,
    health: `${BASE_URL}/health`
};