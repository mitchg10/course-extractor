// const BASE_URL = process.env.NODE_ENV === 'development' 
//   ? 'http://localhost:8000'
//   : '';

// export const endpoints = {
//     process: `${BASE_URL}/process`,
//     status: (taskId) => `${BASE_URL}/status/${taskId}`,
//     availableFiles: (taskId) => `${BASE_URL}/available-files/${taskId}`,
//     download: (taskId, filename) => `${BASE_URL}/download/${taskId}/${filename}`,
//     health: `${BASE_URL}/health`
// };

const BASE_URL = import.meta.env.MODE === 'production'
  ? '' // Empty for production as we're serving from same origin
  : (import.meta.env.VITE_API_URL || 'http://localhost:8000');

export const endpoints = {
    process: `${BASE_URL}/process`,
    status: (taskId) => `${BASE_URL}/status/${taskId}`,
    availableFiles: (taskId) => `${BASE_URL}/available-files/${taskId}`,
    download: (taskId, filename) => `${BASE_URL}/download/${taskId}/${filename}`,
    health: `${BASE_URL}/health`
};