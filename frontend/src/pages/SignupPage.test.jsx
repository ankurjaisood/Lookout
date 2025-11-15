/**
 * Tests for SignupPage
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import SignupPage from './SignupPage';
import { AuthProvider } from '../context/AuthContext';
import * as api from '../services/api';

// Mock the API module
vi.mock('../services/api', () => ({
  authAPI: {
    getMe: vi.fn(),
    signup: vi.fn(),
  },
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('SignupPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.authAPI.getMe.mockResolvedValue({ data: null });
  });

  const renderSignupPage = () => {
    return render(
      <BrowserRouter>
        <AuthProvider>
          <SignupPage />
        </AuthProvider>
      </BrowserRouter>
    );
  };

  it('should render signup form', async () => {
    renderSignupPage();

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /sign up/i })).toBeInTheDocument();
    });

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/display name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign up/i })).toBeInTheDocument();
  });

  it('should show link to login page', async () => {
    renderSignupPage();

    await waitFor(() => {
      expect(screen.getByText(/already have an account/i)).toBeInTheDocument();
    });

    const loginLink = screen.getByRole('link', { name: /login/i });
    expect(loginLink).toBeInTheDocument();
    expect(loginLink).toHaveAttribute('href', '/login');
  });

  it('should handle form input', async () => {
    const user = userEvent.setup();
    renderSignupPage();

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    });

    const emailInput = screen.getByLabelText(/email/i);
    const displayNameInput = screen.getByLabelText(/display name/i);
    const passwordInput = screen.getByLabelText(/password/i);

    await user.type(emailInput, 'newuser@example.com');
    await user.type(displayNameInput, 'New User');
    await user.type(passwordInput, 'password123');

    expect(emailInput).toHaveValue('newuser@example.com');
    expect(displayNameInput).toHaveValue('New User');
    expect(passwordInput).toHaveValue('password123');
  });

  it('should signup successfully and navigate to sessions', async () => {
    const user = userEvent.setup();
    const mockUser = { id: '123', email: 'newuser@example.com', display_name: 'New User' };
    api.authAPI.signup.mockResolvedValue({ data: mockUser });

    renderSignupPage();

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    });

    const emailInput = screen.getByLabelText(/email/i);
    const displayNameInput = screen.getByLabelText(/display name/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const signupButton = screen.getByRole('button', { name: /sign up/i });

    await user.type(emailInput, 'newuser@example.com');
    await user.type(displayNameInput, 'New User');
    await user.type(passwordInput, 'password123');
    await user.click(signupButton);

    await waitFor(() => {
      expect(api.authAPI.signup).toHaveBeenCalledWith(
        'newuser@example.com',
        'password123',
        'New User'
      );
    });

    expect(mockNavigate).toHaveBeenCalledWith('/sessions');
  });

  it('should signup without display name', async () => {
    const user = userEvent.setup();
    const mockUser = { id: '123', email: 'newuser@example.com' };
    api.authAPI.signup.mockResolvedValue({ data: mockUser });

    renderSignupPage();

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    });

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const signupButton = screen.getByRole('button', { name: /sign up/i });

    await user.type(emailInput, 'newuser@example.com');
    await user.type(passwordInput, 'password123');
    await user.click(signupButton);

    await waitFor(() => {
      expect(api.authAPI.signup).toHaveBeenCalledWith('newuser@example.com', 'password123', '');
    });

    expect(mockNavigate).toHaveBeenCalledWith('/sessions');
  });

  it('should display error message on signup failure', async () => {
    const user = userEvent.setup();
    api.authAPI.signup.mockRejectedValue({
      response: {
        data: {
          detail: 'Email already exists',
        },
      },
    });

    renderSignupPage();

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    });

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const signupButton = screen.getByRole('button', { name: /sign up/i });

    await user.type(emailInput, 'existing@example.com');
    await user.type(passwordInput, 'password123');
    await user.click(signupButton);

    await waitFor(() => {
      expect(screen.getByText('Email already exists')).toBeInTheDocument();
    });
  });

  it('should display generic error message when no detail provided', async () => {
    const user = userEvent.setup();
    api.authAPI.signup.mockRejectedValue(new Error('Network error'));

    renderSignupPage();

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    });

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const signupButton = screen.getByRole('button', { name: /sign up/i });

    await user.type(emailInput, 'newuser@example.com');
    await user.type(passwordInput, 'password123');
    await user.click(signupButton);

    await waitFor(() => {
      expect(screen.getByText('Signup failed')).toBeInTheDocument();
    });
  });

  it('should clear error message on new submission', async () => {
    const user = userEvent.setup();
    api.authAPI.signup.mockRejectedValueOnce({
      response: { data: { detail: 'Email already exists' } },
    });
    api.authAPI.signup.mockResolvedValueOnce({ data: { id: '123', email: 'test@example.com' } });

    renderSignupPage();

    await waitFor(() => {
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    });

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const signupButton = screen.getByRole('button', { name: /sign up/i });

    // First attempt - should fail
    await user.type(emailInput, 'existing@example.com');
    await user.type(passwordInput, 'password123');
    await user.click(signupButton);

    await waitFor(() => {
      expect(screen.getByText('Email already exists')).toBeInTheDocument();
    });

    // Second attempt - should succeed and clear error
    await user.clear(emailInput);
    await user.type(emailInput, 'newuser@example.com');
    await user.click(signupButton);

    await waitFor(() => {
      expect(screen.queryByText('Email already exists')).not.toBeInTheDocument();
    });
  });
});
