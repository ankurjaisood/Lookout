/**
 * Tests for AuthContext
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from './AuthContext';
import api from '../services/api';

// Mock the API
vi.mock('../services/api');

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('should provide auth context', () => {
    const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current).toBeDefined();
    expect(result.current.user).toBeNull();
    expect(result.current.loading).toBe(true);
  });

  it('should login successfully', async () => {
    const mockUser = { id: '123', email: 'test@example.com' };
    api.login.mockResolvedValue(mockUser);

    const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.login('test@example.com', 'password123');
    });

    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.loading).toBe(false);
    });
  });

  it('should signup successfully', async () => {
    const mockUser = { id: '123', email: 'test@example.com' };
    api.signup.mockResolvedValue(mockUser);

    const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.signup('test@example.com', 'password123', 'Test User');
    });

    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.loading).toBe(false);
    });
  });

  it('should logout successfully', async () => {
    const mockUser = { id: '123', email: 'test@example.com' };
    api.login.mockResolvedValue(mockUser);
    api.logout.mockResolvedValue({});

    const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
    const { result } = renderHook(() => useAuth(), { wrapper });

    // First login
    await act(async () => {
      await result.current.login('test@example.com', 'password123');
    });

    // Then logout
    await act(async () => {
      await result.current.logout();
    });

    await waitFor(() => {
      expect(result.current.user).toBeNull();
    });
  });

  it('should handle login error', async () => {
    const error = new Error('Invalid credentials');
    api.login.mockRejectedValue(error);

    const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;
    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      try {
        await result.current.login('test@example.com', 'wrong');
      } catch (e) {
        expect(e).toBe(error);
      }
    });

    expect(result.current.user).toBeNull();
  });
});
