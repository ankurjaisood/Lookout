/**
 * Tests for API service
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';
import { authAPI, sessionsAPI, listingsAPI, messagesAPI, clarificationsAPI } from './api';

// Mock axios
vi.mock('axios');

describe('API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('authAPI', () => {
    it('should call signup endpoint with correct data', async () => {
      const mockResponse = { data: { id: '123', email: 'test@example.com' } };
      const mockPost = vi.fn().mockResolvedValue(mockResponse);
      axios.create = vi.fn(() => ({
        post: mockPost,
      }));

      const { authAPI: freshAuthAPI } = await import('./api?update=' + Date.now());

      await freshAuthAPI.signup('test@example.com', 'password123', 'Test User');

      expect(mockPost).toHaveBeenCalledWith('/api/auth/signup', {
        email: 'test@example.com',
        password: 'password123',
        display_name: 'Test User',
      });
    });

    it('should call login endpoint with credentials', async () => {
      const mockResponse = { data: { id: '123', email: 'test@example.com' } };
      const mockPost = vi.fn().mockResolvedValue(mockResponse);
      axios.create = vi.fn(() => ({
        post: mockPost,
      }));

      const { authAPI: freshAuthAPI } = await import('./api?update=' + Date.now());

      await freshAuthAPI.login('test@example.com', 'password123');

      expect(mockPost).toHaveBeenCalledWith('/api/auth/login', {
        email: 'test@example.com',
        password: 'password123',
      });
    });

    it('should call logout endpoint', async () => {
      const mockResponse = { data: { message: 'Logged out' } };
      const mockPost = vi.fn().mockResolvedValue(mockResponse);
      axios.create = vi.fn(() => ({
        post: mockPost,
      }));

      const { authAPI: freshAuthAPI } = await import('./api?update=' + Date.now());

      await freshAuthAPI.logout();

      expect(mockPost).toHaveBeenCalledWith('/api/auth/logout');
    });

    it('should call getMe endpoint', async () => {
      const mockResponse = { data: { id: '123', email: 'test@example.com' } };
      const mockGet = vi.fn().mockResolvedValue(mockResponse);
      axios.create = vi.fn(() => ({
        get: mockGet,
      }));

      const { authAPI: freshAuthAPI } = await import('./api?update=' + Date.now());

      await freshAuthAPI.getMe();

      expect(mockGet).toHaveBeenCalledWith('/api/auth/me');
    });
  });

  describe('sessionsAPI', () => {
    it('should create session with requirements data', async () => {
      const mockResponse = { data: { id: 'session-123' } };
      const mockPost = vi.fn().mockResolvedValue(mockResponse);
      axios.create = vi.fn(() => ({
        post: mockPost,
      }));

      const { sessionsAPI: freshSessionsAPI } = await import('./api?update=' + Date.now());

      await freshSessionsAPI.create('My Session', 'cars', 'Manual only');

      expect(mockPost).toHaveBeenCalledWith('/api/sessions', {
        title: 'My Session',
        category: 'cars',
        requirements: 'Manual only',
      });
    });

    it('should list all sessions', async () => {
      const mockResponse = { data: [] };
      const mockGet = vi.fn().mockResolvedValue(mockResponse);
      axios.create = vi.fn(() => ({
        get: mockGet,
      }));

      const { sessionsAPI: freshSessionsAPI } = await import('./api?update=' + Date.now());

      await freshSessionsAPI.list();

      expect(mockGet).toHaveBeenCalledWith('/api/sessions');
    });

    it('should get session by id', async () => {
      const mockResponse = { data: { id: 'session-123' } };
      const mockGet = vi.fn().mockResolvedValue(mockResponse);
      axios.create = vi.fn(() => ({
        get: mockGet,
      }));

      const { sessionsAPI: freshSessionsAPI } = await import('./api?update=' + Date.now());

      await freshSessionsAPI.get('session-123');

      expect(mockGet).toHaveBeenCalledWith('/api/sessions/session-123');
    });

    it('should delete session by id', async () => {
      const mockResponse = { data: { message: 'Deleted' } };
      const mockDelete = vi.fn().mockResolvedValue(mockResponse);
      axios.create = vi.fn(() => ({
        delete: mockDelete,
      }));

      const { sessionsAPI: freshSessionsAPI } = await import('./api?update=' + Date.now());

      await freshSessionsAPI.delete('session-123');

      expect(mockDelete).toHaveBeenCalledWith('/api/sessions/session-123');
    });

    it('should get session state', async () => {
      const mockResponse = { data: { session: {}, messages: [], listings: [] } };
      const mockGet = vi.fn().mockResolvedValue(mockResponse);
      axios.create = vi.fn(() => ({
        get: mockGet,
      }));

      const { sessionsAPI: freshSessionsAPI } = await import('./api?update=' + Date.now());

      await freshSessionsAPI.getState('session-123');

      expect(mockGet).toHaveBeenCalledWith('/api/sessions/session-123/state');
    });

    it('should update session with payload', async () => {
      const mockResponse = { data: { id: 'session-123' } };
      const mockPatch = vi.fn().mockResolvedValue(mockResponse);
      axios.create = vi.fn(() => ({
        patch: mockPatch,
      }));

      const { sessionsAPI: freshSessionsAPI } = await import('./api?update=' + Date.now());

      await freshSessionsAPI.update('session-123', { requirements: 'Manual hardtop' });

      expect(mockPatch).toHaveBeenCalledWith('/api/sessions/session-123', {
        requirements: 'Manual hardtop',
      });
    });
  });

  describe('listingsAPI', () => {
    it('should create listing with data', async () => {
      const listingData = { title: 'Test Listing', price: 100 };
      const mockResponse = { data: { id: 'listing-123' } };
      const mockPost = vi.fn().mockResolvedValue(mockResponse);
      axios.create = vi.fn(() => ({
        post: mockPost,
      }));

      const { listingsAPI: freshListingsAPI } = await import('./api?update=' + Date.now());

      await freshListingsAPI.create('session-123', listingData);

      expect(mockPost).toHaveBeenCalledWith('/api/sessions/session-123/listings', listingData);
    });

    it('should list listings for session', async () => {
      const mockResponse = { data: [] };
      const mockGet = vi.fn().mockResolvedValue(mockResponse);
      axios.create = vi.fn(() => ({
        get: mockGet,
      }));

      const { listingsAPI: freshListingsAPI } = await import('./api?update=' + Date.now());

      await freshListingsAPI.list('session-123');

      expect(mockGet).toHaveBeenCalledWith('/api/sessions/session-123/listings');
    });

    it('should mark listing as removed', async () => {
      const mockResponse = { data: { message: 'Removed' } };
      const mockPatch = vi.fn().mockResolvedValue(mockResponse);
      axios.create = vi.fn(() => ({
        patch: mockPatch,
      }));

      const { listingsAPI: freshListingsAPI } = await import('./api?update=' + Date.now());

      await freshListingsAPI.markRemoved('session-123', 'listing-456');

      expect(mockPatch).toHaveBeenCalledWith('/api/sessions/session-123/listings/listing-456');
    });

    it('should request listing reevaluation', async () => {
      const mockResponse = { data: { id: 'listing-456', score: 80 } };
      const mockPost = vi.fn().mockResolvedValue(mockResponse);
      axios.create = vi.fn(() => ({
        post: mockPost,
      }));

      const { listingsAPI: freshListingsAPI } = await import('./api?update=' + Date.now());

      await freshListingsAPI.reevaluate('session-123', 'listing-456');

      expect(mockPost).toHaveBeenCalledWith('/api/sessions/session-123/listings/listing-456/reevaluate');
    });

    it('should update listing', async () => {
      const mockResponse = { data: { id: 'listing-456', title: 'Updated' } };
      const mockPut = vi.fn().mockResolvedValue(mockResponse);
      axios.create = vi.fn(() => ({
        put: mockPut,
      }));

      const { listingsAPI: freshListingsAPI } = await import('./api?update=' + Date.now());

      await freshListingsAPI.update('session-123', 'listing-456', { title: 'Updated' });

      expect(mockPut).toHaveBeenCalledWith(
        '/api/sessions/session-123/listings/listing-456',
        { title: 'Updated' }
      );
    });
  });

  describe('messagesAPI', () => {
    it('should send message with text', async () => {
      const mockResponse = { data: { id: 'msg-123' } };
      const mockPost = vi.fn().mockResolvedValue(mockResponse);
      axios.create = vi.fn(() => ({
        post: mockPost,
      }));

      const { messagesAPI: freshMessagesAPI } = await import('./api?update=' + Date.now());

      await freshMessagesAPI.send('session-123', 'Hello agent');

      expect(mockPost).toHaveBeenCalledWith('/api/sessions/session-123/messages', {
        text: 'Hello agent',
      });
    });

    it('should list messages for session', async () => {
      const mockResponse = { data: [] };
      const mockGet = vi.fn().mockResolvedValue(mockResponse);
      axios.create = vi.fn(() => ({
        get: mockGet,
      }));

      const { messagesAPI: freshMessagesAPI } = await import('./api?update=' + Date.now());

      await freshMessagesAPI.list('session-123');

      expect(mockGet).toHaveBeenCalledWith('/api/sessions/session-123/messages');
    });
  });

  describe('clarificationsAPI', () => {
    it('should submit clarification answer', async () => {
      const mockResponse = { data: { id: 'msg-clar-answer' } };
      const mockPost = vi.fn().mockResolvedValue(mockResponse);
      axios.create = vi.fn(() => ({
        post: mockPost,
      }));

      const { clarificationsAPI: freshClarificationsAPI } = await import('./api?update=' + Date.now());

      await freshClarificationsAPI.answer('session-123', 'clar-456', 'It has 50k miles');

      expect(mockPost).toHaveBeenCalledWith(
        '/api/sessions/session-123/clarifications/clar-456/answer',
        { text: 'It has 50k miles' }
      );
    });
  });
});
