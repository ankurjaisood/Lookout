/**
 * Tests for API service
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';
import api from './api';

// Mock axios
vi.mock('axios');

describe('API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Auth API', () => {
    it('should call signup endpoint', async () => {
      const mockData = { id: '123', email: 'test@example.com' };
      axios.post.mockResolvedValue({ data: mockData });

      const result = await api.signup('test@example.com', 'password123', 'Test User');

      expect(axios.post).toHaveBeenCalledWith('/api/auth/signup', {
        email: 'test@example.com',
        password: 'password123',
        display_name: 'Test User'
      });
      expect(result).toEqual(mockData);
    });

    it('should call login endpoint', async () => {
      const mockData = { id: '123', email: 'test@example.com' };
      axios.post.mockResolvedValue({ data: mockData });

      const result = await api.login('test@example.com', 'password123');

      expect(axios.post).toHaveBeenCalledWith('/api/auth/login', {
        email: 'test@example.com',
        password: 'password123'
      });
      expect(result).toEqual(mockData);
    });

    it('should call logout endpoint', async () => {
      axios.post.mockResolvedValue({ data: { message: 'Logged out' } });

      await api.logout();

      expect(axios.post).toHaveBeenCalledWith('/api/auth/logout');
    });

    it('should call getCurrentUser endpoint', async () => {
      const mockData = { id: '123', email: 'test@example.com' };
      axios.get.mockResolvedValue({ data: mockData });

      const result = await api.getCurrentUser();

      expect(axios.get).toHaveBeenCalledWith('/api/auth/me');
      expect(result).toEqual(mockData);
    });
  });

  describe('Session API', () => {
    it('should create a session', async () => {
      const mockData = { id: 'session123', title: 'Find a car' };
      axios.post.mockResolvedValue({ data: mockData });

      const result = await api.createSession('Find a car', 'cars');

      expect(axios.post).toHaveBeenCalledWith('/api/sessions', {
        title: 'Find a car',
        category: 'cars'
      });
      expect(result).toEqual(mockData);
    });

    it('should list sessions', async () => {
      const mockData = [
        { id: 'session1', title: 'Session 1' },
        { id: 'session2', title: 'Session 2' }
      ];
      axios.get.mockResolvedValue({ data: mockData });

      const result = await api.listSessions();

      expect(axios.get).toHaveBeenCalledWith('/api/sessions');
      expect(result).toEqual(mockData);
    });

    it('should get session state', async () => {
      const mockData = {
        session: { id: 'session123' },
        messages: [],
        listings: []
      };
      axios.get.mockResolvedValue({ data: mockData });

      const result = await api.getSessionState('session123');

      expect(axios.get).toHaveBeenCalledWith('/api/sessions/session123/state');
      expect(result).toEqual(mockData);
    });

    it('should delete a session', async () => {
      axios.delete.mockResolvedValue({});

      await api.deleteSession('session123');

      expect(axios.delete).toHaveBeenCalledWith('/api/sessions/session123');
    });
  });

  describe('Listing API', () => {
    it('should create a listing', async () => {
      const mockData = { id: 'listing123', title: '2014 Mazda Miata' };
      const listingData = {
        title: '2014 Mazda Miata',
        url: 'https://example.com',
        price: 13500,
        currency: 'USD',
        marketplace: 'Craigslist',
        listing_metadata: { mileage: 78000 }
      };
      axios.post.mockResolvedValue({ data: mockData });

      const result = await api.createListing('session123', listingData);

      expect(axios.post).toHaveBeenCalledWith(
        '/api/sessions/session123/listings',
        listingData
      );
      expect(result).toEqual(mockData);
    });

    it('should mark listing as removed', async () => {
      const mockData = { id: 'listing123', status: 'removed' };
      axios.patch.mockResolvedValue({ data: mockData });

      const result = await api.markListingRemoved('session123', 'listing123');

      expect(axios.patch).toHaveBeenCalledWith(
        '/api/sessions/session123/listings/listing123'
      );
      expect(result).toEqual(mockData);
    });
  });

  describe('Message API', () => {
    it('should send a message', async () => {
      const mockData = { id: 'msg123', text: 'Hello', sender: 'user' };
      axios.post.mockResolvedValue({ data: mockData });

      const result = await api.sendMessage('session123', 'Hello');

      expect(axios.post).toHaveBeenCalledWith(
        '/api/sessions/session123/messages',
        { text: 'Hello' }
      );
      expect(result).toEqual(mockData);
    });

    it('should get messages', async () => {
      const mockData = [
        { id: 'msg1', text: 'Hello' },
        { id: 'msg2', text: 'Hi there' }
      ];
      axios.get.mockResolvedValue({ data: mockData });

      const result = await api.getMessages('session123');

      expect(axios.get).toHaveBeenCalledWith('/api/sessions/session123/messages');
      expect(result).toEqual(mockData);
    });
  });
});
