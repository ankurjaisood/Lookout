/**
 * Tests for SessionsPage
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import SessionsPage from './SessionsPage';
import { AuthProvider } from '../context/AuthContext';
import * as api from '../services/api';

// Mock the API module
vi.mock('../services/api', () => ({
  authAPI: {
    getMe: vi.fn(),
    logout: vi.fn(),
  },
  sessionsAPI: {
    list: vi.fn(),
    create: vi.fn(),
    delete: vi.fn(),
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

// Mock window.confirm
global.confirm = vi.fn();

describe('SessionsPage', () => {
  const mockUser = { id: '123', email: 'test@example.com' };
  const mockSessions = [
    {
      id: 'session-1',
      title: 'Find a used Miata',
      category: 'cars',
      status: 'ACTIVE',
      created_at: '2025-01-15T10:00:00Z',
    },
    {
      id: 'session-2',
      title: 'Laptop search',
      category: 'laptops',
      status: 'WAITING_FOR_CLARIFICATION',
      created_at: '2025-01-16T10:00:00Z',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    api.authAPI.getMe.mockResolvedValue({ data: mockUser });
    api.sessionsAPI.list.mockResolvedValue({ data: mockSessions });
    global.confirm.mockReturnValue(true);
  });

  const renderSessionsPage = () => {
    return render(
      <BrowserRouter>
        <AuthProvider>
          <SessionsPage />
        </AuthProvider>
      </BrowserRouter>
    );
  };

  it('should show loading state initially', () => {
    renderSessionsPage();
    expect(screen.getByText(/loading sessions/i)).toBeInTheDocument();
  });

  it('should load and display sessions', async () => {
    renderSessionsPage();

    await waitFor(() => {
      expect(api.sessionsAPI.list).toHaveBeenCalled();
    });

    expect(screen.getByText('Find a used Miata')).toBeInTheDocument();
    expect(screen.getByText('Laptop search')).toBeInTheDocument();
  });

  it('should display user email and logout button', async () => {
    renderSessionsPage();

    await waitFor(() => {
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
    });

    expect(screen.getByRole('button', { name: /logout/i })).toBeInTheDocument();
  });

  it('should show empty state when no sessions', async () => {
    api.sessionsAPI.list.mockResolvedValue({ data: [] });

    renderSessionsPage();

    await waitFor(() => {
      expect(screen.getByText(/no sessions yet/i)).toBeInTheDocument();
    });
  });

  it('should show status badge for waiting sessions', async () => {
    renderSessionsPage();

    await waitFor(() => {
      expect(screen.getByText(/waiting for answer/i)).toBeInTheDocument();
    });
  });

  it('should toggle create session form', async () => {
    const user = userEvent.setup();
    renderSessionsPage();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /new session/i })).toBeInTheDocument();
    });

    const newSessionButton = screen.getByRole('button', { name: /new session/i });

    // Click to show form
    await user.click(newSessionButton);
    expect(screen.getByPlaceholderText(/session title/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();

    // Click to hide form
    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    await user.click(cancelButton);
    expect(screen.queryByPlaceholderText(/session title/i)).not.toBeInTheDocument();
  });

  it('should create new session and navigate to it', async () => {
    const user = userEvent.setup();
    const newSession = { id: 'session-3', title: 'New Session', category: 'cars' };
    api.sessionsAPI.create.mockResolvedValue({ data: newSession });

    renderSessionsPage();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /new session/i })).toBeInTheDocument();
    });

    // Open create form
    const newSessionButton = screen.getByRole('button', { name: /new session/i });
    await user.click(newSessionButton);

    // Fill form
    const titleInput = screen.getByPlaceholderText(/session title/i);
    const categorySelect = screen.getByRole('combobox');
    const createButton = screen.getByRole('button', { name: /^create$/i });

    await user.type(titleInput, 'New Session');
    await user.selectOptions(categorySelect, 'laptops');
    await user.click(createButton);

    await waitFor(() => {
      expect(api.sessionsAPI.create).toHaveBeenCalledWith('New Session', 'laptops');
    });

    expect(mockNavigate).toHaveBeenCalledWith('/sessions/session-3');
  });

  it('should navigate to session when clicked', async () => {
    const user = userEvent.setup();
    renderSessionsPage();

    await waitFor(() => {
      expect(screen.getByText('Find a used Miata')).toBeInTheDocument();
    });

    const sessionCard = screen.getByText('Find a used Miata').closest('.session-info');
    await user.click(sessionCard);

    expect(mockNavigate).toHaveBeenCalledWith('/sessions/session-1');
  });

  it('should delete session with confirmation', async () => {
    const user = userEvent.setup();
    api.sessionsAPI.delete.mockResolvedValue({ data: { message: 'Deleted' } });
    api.sessionsAPI.list
      .mockResolvedValueOnce({ data: mockSessions })
      .mockResolvedValueOnce({ data: [mockSessions[0]] });

    renderSessionsPage();

    await waitFor(() => {
      expect(screen.getByText('Find a used Miata')).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
    await user.click(deleteButtons[0]);

    expect(global.confirm).toHaveBeenCalledWith('Are you sure you want to delete this session?');

    await waitFor(() => {
      expect(api.sessionsAPI.delete).toHaveBeenCalledWith('session-1');
    });

    await waitFor(() => {
      expect(api.sessionsAPI.list).toHaveBeenCalledTimes(2);
    });
  });

  it('should not delete session if confirmation is cancelled', async () => {
    const user = userEvent.setup();
    global.confirm.mockReturnValue(false);

    renderSessionsPage();

    await waitFor(() => {
      expect(screen.getByText('Find a used Miata')).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
    await user.click(deleteButtons[0]);

    expect(global.confirm).toHaveBeenCalled();
    expect(api.sessionsAPI.delete).not.toHaveBeenCalled();
  });

  it('should handle logout', async () => {
    const user = userEvent.setup();
    api.authAPI.logout.mockResolvedValue({ data: { message: 'Logged out' } });

    renderSessionsPage();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /logout/i })).toBeInTheDocument();
    });

    const logoutButton = screen.getByRole('button', { name: /logout/i });
    await user.click(logoutButton);

    await waitFor(() => {
      expect(api.authAPI.logout).toHaveBeenCalled();
    });
  });

  it('should handle error loading sessions', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    api.sessionsAPI.list.mockRejectedValue(new Error('Network error'));

    renderSessionsPage();

    await waitFor(() => {
      expect(screen.getByText(/no sessions yet/i)).toBeInTheDocument();
    });

    expect(consoleErrorSpy).toHaveBeenCalledWith(
      'Failed to load sessions:',
      expect.any(Error)
    );

    consoleErrorSpy.mockRestore();
  });

  it('should handle error creating session', async () => {
    const user = userEvent.setup();
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    api.sessionsAPI.create.mockRejectedValue(new Error('Create failed'));

    renderSessionsPage();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /new session/i })).toBeInTheDocument();
    });

    // Open and fill form
    const newSessionButton = screen.getByRole('button', { name: /new session/i });
    await user.click(newSessionButton);

    const titleInput = screen.getByPlaceholderText(/session title/i);
    const createButton = screen.getByRole('button', { name: /^create$/i });

    await user.type(titleInput, 'Test Session');
    await user.click(createButton);

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Failed to create session:',
        expect.any(Error)
      );
    });

    consoleErrorSpy.mockRestore();
  });
});
