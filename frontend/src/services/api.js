/**
 * API Service for Lookout backend
 * Handles all HTTP requests to the backend API
 */
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  withCredentials: true, // Important for session cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auth API
export const authAPI = {
  signup: (email, password, displayName) =>
    api.post('/api/auth/signup', { email, password, display_name: displayName }),

  login: (email, password) =>
    api.post('/api/auth/login', { email, password }),

  logout: () =>
    api.post('/api/auth/logout'),

  getMe: () =>
    api.get('/api/auth/me'),
};

// Sessions API
export const sessionsAPI = {
  create: (title, category) =>
    api.post('/api/sessions', { title, category }),

  list: () =>
    api.get('/api/sessions'),

  get: (sessionId) =>
    api.get(`/api/sessions/${sessionId}`),

  delete: (sessionId) =>
    api.delete(`/api/sessions/${sessionId}`),

  getState: (sessionId) =>
    api.get(`/api/sessions/${sessionId}/state`),
};

// Listings API
export const listingsAPI = {
  create: (sessionId, listingData) =>
    api.post(`/api/sessions/${sessionId}/listings`, listingData),

  list: (sessionId) =>
    api.get(`/api/sessions/${sessionId}/listings`),

  markRemoved: (sessionId, listingId) =>
    api.patch(`/api/sessions/${sessionId}/listings/${listingId}`),
};

// Messages API
export const messagesAPI = {
  send: (sessionId, text) =>
    api.post(`/api/sessions/${sessionId}/messages`, { text }),

  list: (sessionId) =>
    api.get(`/api/sessions/${sessionId}/messages`),
};

export default api;
