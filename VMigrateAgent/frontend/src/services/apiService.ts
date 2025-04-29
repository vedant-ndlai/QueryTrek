import axios, { AxiosResponse, AxiosError, InternalAxiosRequestConfig } from 'axios';

// Create an axios instance with default config
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
interface ConnectionData {
  connection_string: string;
  database_type: string;
}

interface SchemaData {
  connection_string: string;
  schema_filter?: string[];
}

interface AnalysisOptions {
  type: string;
  parameters?: Record<string, unknown>;
}

interface Settings {
  [key: string]: unknown;
}

interface QueryConversionData {
  source_query: string;
  source_language: string;
  target_language: string;
}

// API service methods
export const apiService = {
  // Database connections
  getDatabases: () => api.get<any[]>('/api/databases'),
  connectDatabase: (connectionData: ConnectionData) => api.post<any>('/api/databases/connect', connectionData),
  testConnection: (connectionData: ConnectionData) => api.post<{message: string}>('/api/databases/test', connectionData),
  
  // Schema operations
  getSchemas: () => api.get<any[]>('/api/schemas'),
  getSchemaDetails: (schemaId: string) => api.get<any>(`/api/schemas/${schemaId}`),
  extractSchema: (data: SchemaData) => api.post<{message: string}>(`/api/schemas/extract`, data),
  
  // Analysis operations
  getAnalyses: () => api.get<any[]>('/api/analyses'),
  getAnalysisDetails: (analysisId: string) => api.get<any>(`/api/analyses/${analysisId}`),
  runAnalysis: (schemaId: string, options: AnalysisOptions) => 
    api.post<any>('/api/analyses/run', { schemaId, options }),
  
  // Dashboard data
  getDashboardStats: () => api.get<any>('/api/dashboard/stats'),

  // Code conversion
  convertQuery: (data: QueryConversionData) => api.post<any>('/convert-query', data),
  
  // Settings
  getSettings: () => api.get<Settings>('/api/settings'),
  updateSettings: (settings: Settings) => api.put<Settings>('/api/settings', settings),
};

// Request interceptor for adding auth token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // You can add auth token here if needed
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError) => {
    // Handle common errors here
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export default api;
