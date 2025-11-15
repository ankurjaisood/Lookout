import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { sessionsAPI } from '../services/api';

export default function SessionsPage() {
  const [sessions, setSessions] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('cars');
  const [loading, setLoading] = useState(true);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const response = await sessionsAPI.list();
      setSessions(response.data);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSession = async (e) => {
    e.preventDefault();
    try {
      const response = await sessionsAPI.create(title, category);
      navigate(`/sessions/${response.data.id}`);
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const handleDeleteSession = async (sessionId) => {
    if (!confirm('Are you sure you want to delete this session?')) return;

    try {
      await sessionsAPI.delete(sessionId);
      loadSessions();
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  if (loading) return <div className="loading">Loading sessions...</div>;

  return (
    <div className="sessions-page">
      <header className="page-header">
        <h1>Lookout</h1>
        <div className="user-info">
          <span>{user?.email}</span>
          <button onClick={logout} className="btn-secondary">Logout</button>
        </div>
      </header>

      <div className="page-content">
        <div className="sessions-header">
          <h2>Your Sessions</h2>
          <button onClick={() => setShowCreateForm(!showCreateForm)} className="btn-primary">
            {showCreateForm ? 'Cancel' : 'New Session'}
          </button>
        </div>

        {showCreateForm && (
          <form onSubmit={handleCreateSession} className="create-session-form">
            <input
              type="text"
              placeholder="Session title (e.g., 'Find a used Miata')"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
            <select value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="cars">Cars</option>
              <option value="laptops">Laptops</option>
              <option value="electronics">Electronics</option>
              <option value="furniture">Furniture</option>
              <option value="other">Other</option>
            </select>
            <button type="submit" className="btn-primary">Create</button>
          </form>
        )}

        <div className="sessions-list">
          {sessions.length === 0 ? (
            <p className="empty-state">No sessions yet. Create one to get started!</p>
          ) : (
            sessions.map((session) => (
              <div key={session.id} className="session-card">
                <div onClick={() => navigate(`/sessions/${session.id}`)} className="session-info">
                  <h3>{session.title}</h3>
                  <p className="session-meta">
                    {session.category} • {new Date(session.created_at).toLocaleDateString()}
                  </p>
                  {session.status === 'WAITING_FOR_CLARIFICATION' && (
                    <span className="status-badge">Waiting for answer</span>
                  )}
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteSession(session.id);
                  }}
                  className="btn-danger"
                >
                  Delete
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
