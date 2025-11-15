/**
 * Tests for AuthContext
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, renderHook, act } from '@testing-library/react';
import { AuthProvider, useAuth } from './AuthContext';
import * as api from '../services/api';

// Mock the API module
vi.mock('../services/api', () => ({
  authAPI: {
    getMe: vi.fn(),
    login: vi.fn(),
    signup: vi.fn(),
    logout: vi.fn(),
  },
}));

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('AuthProvider', () => {
    it('should check authentication on mount', async () => {
      const mockUser = { id: '123', email: 'test@example.com' };
      api.authAPI.getMe.mockResolvedValue({ data: mockUser });

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      });

      // Initially loading
      expect(result.current.loading).toBe(true);

      // Wait for auth check
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
      expect(api.authAPI.getMe).toHaveBeenCalledTimes(1);
    });

    it('should set user to null if not authenticated', async () => {
      api.authAPI.getMe.mockRejectedValue(new Error('Unauthorized'));

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('should login successfully', async () => {
      const mockUser = { id: '123', email: 'test@example.com' };
      api.authAPI.getMe.mockResolvedValue({ data: null });
      api.authAPI.login.mockResolvedValue({ data: mockUser });

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Perform login
      await act(async () => {
        await result.current.login('test@example.com', 'password123');
      });

      expect(api.authAPI.login).toHaveBeenCalledWith('test@example.com', 'password123');
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
    });

    it('should signup successfully', async () => {
      const mockUser = { id: '123', email: 'newuser@example.com' };
      api.authAPI.getMe.mockResolvedValue({ data: null });
      api.authAPI.signup.mockResolvedValue({ data: mockUser });

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // Perform signup
      await act(async () => {
        await result.current.signup('newuser@example.com', 'password123', 'New User');
      });

      expect(api.authAPI.signup).toHaveBeenCalledWith(
        'newuser@example.com',
        'password123',
        'New User'
      );
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
    });

    it('should logout successfully', async () => {
      const mockUser = { id: '123', email: 'test@example.com' };
      api.authAPI.getMe.mockResolvedValue({ data: mockUser });
      api.authAPI.logout.mockResolvedValue({ data: { message: 'Logged out' } });

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.user).toEqual(mockUser);

      // Perform logout
      await act(async () => {
        await result.current.logout();
      });

      expect(api.authAPI.logout).toHaveBeenCalledTimes(1);
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('useAuth', () => {
    it('should throw error when used outside AuthProvider', () => {
      // Suppress console.error for this test
      const originalError = console.error;
      console.error = vi.fn();

      expect(() => {
        renderHook(() => useAuth());
      }).toThrow('useAuth must be used within AuthProvider');

      console.error = originalError;
    });

    it('should provide auth context when used within AuthProvider', async () => {
      api.authAPI.getMe.mockResolvedValue({ data: null });

      const { result } = renderHook(() => useAuth(), {
        wrapper: AuthProvider,
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current).toHaveProperty('user');
      expect(result.current).toHaveProperty('login');
      expect(result.current).toHaveProperty('signup');
      expect(result.current).toHaveProperty('logout');
      expect(result.current).toHaveProperty('loading');
      expect(result.current).toHaveProperty('isAuthenticated');
    });
  });
});
