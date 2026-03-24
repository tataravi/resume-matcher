import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiService {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add token to requests
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('authToken');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Handle auth errors
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('authToken');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth methods
  async login(email, password) {
    const response = await this.client.post('/auth/login', { email, password });
    const { access_token } = response.data;
    localStorage.setItem('authToken', access_token);
    return response.data;
  }

  async register(email, password, fullName) {
    return await this.client.post('/auth/register', {
      email,
      password,
      full_name: fullName,
    });
  }

  async getDemoToken() {
    const response = await this.client.post('/auth/demo-token');
    const { access_token } = response.data;
    localStorage.setItem('authToken', access_token);
    return response.data;
  }

  async verifyToken() {
    return await this.client.get('/auth/verify');
  }

  // File upload methods
  async uploadResume(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    return await this.client.post('/api/v1/upload/resume', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  async uploadDemo(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    return await this.client.post('/api/v1/upload/demo', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  async getUploadedFiles() {
    return await this.client.get('/api/v1/upload/resume/list');
  }

  async previewFile(fileId) {
    return await this.client.get(`/api/v1/upload/resume/${fileId}/preview`);
  }

  async deleteFile(fileId) {
    return await this.client.delete(`/api/v1/upload/resume/${fileId}`);
  }

  // Analysis methods
  async startAnalysis(analysisRequest) {
    return await this.client.post('/api/v1/analysis/start', analysisRequest);
  }

  async startAnalysisFromFile(fileAnalysisRequest) {
    return await this.client.post('/api/v1/analysis/start-from-file', fileAnalysisRequest);
  }

  async getAnalysisStatus(analysisId) {
    return await this.client.get(`/api/v1/analysis/status/${analysisId}`);
  }

  async getAnalysisResults(analysisId) {
    return await this.client.get(`/api/v1/analysis/result/${analysisId}`);
  }

  async getAnalyses() {
    return await this.client.get('/api/v1/analysis/list');
  }

  async cancelAnalysis(analysisId) {
    return await this.client.delete(`/api/v1/analysis/cancel/${analysisId}`);
  }

  // Utility methods
  logout() {
    localStorage.removeItem('authToken');
    window.location.href = '/login';
  }

  isAuthenticated() {
    return !!localStorage.getItem('authToken');
  }
}

export default new ApiService();