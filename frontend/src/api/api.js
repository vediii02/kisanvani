import axios from 'axios';

// -------------------------------
// API Base URL
// -------------------------------
const API_BASE_URL = (() => {
  // Production domain → Nginx already handles /api/
  if (window.location.hostname === 'kisan.rechargestudio.com') {
    return '/api'; // Nginx routes /api/ to backend
  }
  // Localhost / IP / env variable
  return process.env.REACT_APP_BACKEND_URL || `http://${window.location.hostname}:8001/api`;
})();

// -------------------------------
// Axios instance
// -------------------------------
const api = axios.create({
  baseURL: API_BASE_URL,  // <-- Don't add /api here
  headers: {
    'Content-Type': 'application/json',
  },
});

// -------------------------------
// Request interceptor → attach token
// -------------------------------
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// -------------------------------
// Response interceptor → handle token expiration
// -------------------------------
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// -------------------------------
// Auth endpoints
// -------------------------------
export const login = (credentials) => api.post('/auth/login', credentials);
export const register = (userData) => api.post('/auth/register', userData);
export const getMe = () => api.get('/auth/me');

// -------------------------------
// Admin endpoints
// -------------------------------
export const adminAPI = {
  getDashboardStats: () => api.get('/admin/stats'),
  getEscalations: (params) => api.get('/admin/escalations', { params }),
};

// -------------------------------
// Calls API
// -------------------------------
export const callsAPI = {
  getCalls: (params) => api.get('/calls', { params }),
  getCallById: (id) => api.get(`/calls/${id}`),
  createCall: (data) => api.post('/calls', data),
};

// -------------------------------
// Knowledge Base API
// -------------------------------
export const kbAPI = {
  getEntries: (params) => api.get('/kb/entries', { params }),
  createEntry: (data) => api.post('/kb/entries', data),
  updateEntry: (id, data) => api.put(`/kb/entries/${id}`, data),
  deleteEntry: (id) => api.delete(`/kb/entries/${id}`),
};

// -------------------------------
// Super Admin API
// -------------------------------
export const superAdminAPI = {
  getUsers: (skip = 0, limit = 100) => api.get(`/superadmin/users?skip=${skip}&limit=${limit}`),
  getUser: (userId) => api.get(`/superadmin/users/${userId}`),
  createUser: (userData) => api.post('/superadmin/users', userData),
  updateUser: (userId, userData) => api.put(`/superadmin/users/${userId}`, userData),
  deleteUser: (userId) => api.delete(`/superadmin/users/${userId}`),
  resetPassword: (userId, newPassword) =>
    api.post(`/superadmin/users/${userId}/reset-password`, { new_password: newPassword }),
  getStats: () => api.get('/superadmin/dashboard/stats'),
};

// -------------------------------
// Organisation API
// -------------------------------
export const organisationAPI = {
  getAll: (skip = 0, limit = 100) => api.get(`/organisations?skip=${skip}&limit=${limit}`),
  get: (orgId) => api.get(`/organisations/${orgId}`),
  create: (data) => api.post('/organisations', data),
  update: (orgId, data) => api.put(`/organisations/${orgId}`, data),
  delete: (orgId) => api.delete(`/organisations/${orgId}`),
  getPhones: (orgId) => api.get(`/organisations/${orgId}/phones`),
  addPhone: (orgId, data) => api.post(`/organisations/${orgId}/phones`, data),
  removePhone: (orgId, phoneId) => api.delete(`/organisations/${orgId}/phones/${phoneId}`),
  lookupPhone: (phoneNumber) => api.get(`/organisations/lookup/${phoneNumber}`),
};

// -------------------------------
// Brand API
// -------------------------------
export const brandAPI = {
  getAll: (skip = 0, limit = 100) => api.get(`/brands?skip=${skip}&limit=${limit}`),
  get: (brandId) => api.get(`/brands/${brandId}`),
  create: (data) => api.post('/brands', data),
  update: (brandId, data) => api.put(`/brands/${brandId}`, data),
  delete: (brandId) => api.delete(`/brands/${brandId}`),
  getByOrganisation: (orgId) => api.get(`/brands/organisation/${orgId}`),
};

// -------------------------------
// Product API
// -------------------------------
export const productAPI = {
  getAll: (skip = 0, limit = 100) => api.get(`/products?skip=${skip}&limit=${limit}`),
  get: (productId) => api.get(`/products/${productId}`),
  create: (data) => api.post('/products', data),
  update: (productId, data) => api.put(`/products/${productId}`, data),
  delete: (productId) => api.delete(`/products/${productId}`),
  getByBrand: (brandId) => api.get(`/products/brand/${brandId}`),
  getByOrganisation: (orgId) => api.get(`/products/organisation/${orgId}`),
};

// -------------------------------
// Document Ingestion API
// -------------------------------
export const ingestAPI = {
  uploadDocument: (companyId, file) => {
    const formData = new FormData();
    formData.append('company_id', companyId);
    formData.append('file', file);
    return api.post('/ingest/file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  deleteCompanyData: (companyId) => api.delete(`/ingest/company/${companyId}`),
};

export default api;