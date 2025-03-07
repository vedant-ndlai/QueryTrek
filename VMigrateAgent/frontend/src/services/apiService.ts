import axios from 'axios';

// Create an axios instance with default config
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// API service methods
export const apiService = {
  // Database connections
  getDatabases: () => api.get('/api/databases'),
  connectDatabase: (connectionData: any) => api.post('/api/databases/connect', connectionData),
  testConnection: (connectionData: any) => api.post('/api/databases/test', connectionData),
  
  // Schema operations
  getSchemas: () => api.get('/api/schemas'),
  getSchemaDetails: (schemaId: string) => api.get(`/api/schemas/${schemaId}`),
  extractSchema: (databaseId: string) => api.post(`/api/schemas/extract`, { databaseId }),
  
  // Analysis operations
  getAnalyses: () => api.get('/api/analyses'),
  getAnalysisDetails: (analysisId: string) => api.get(`/api/analyses/${analysisId}`),
  runAnalysis: (schemaId: string, options: any) => api.post('/api/analyses/run', { schemaId, options }),
  
  // Dashboard data
  getDashboardStats: () => api.get('/api/dashboard/stats'),
  
  // Settings
  getSettings: () => api.get('/api/settings'),
  updateSettings: (settings: any) => api.put('/api/settings', settings),
};

// Request interceptor for adding auth token
api.interceptors.request.use(
  (config) => {
    // You can add auth token here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle common errors here
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export default api;
