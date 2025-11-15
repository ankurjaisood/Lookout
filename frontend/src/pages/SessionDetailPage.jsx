import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { sessionsAPI, listingsAPI, messagesAPI } from '../services/api';

const DEAL_LABELS = {
  0: 'Horrible deal',
  21: 'Poor deal',
  41: 'Fair deal',
  61: 'Good deal',
  81: 'Great deal',
};

function getDealLabel(score) {
  if (score === null || score === undefined) return 'Not evaluated';
  if (score >= 81) return 'Great deal';
  if (score >= 61) return 'Good deal';
  if (score >= 41) return 'Fair deal';
  if (score >= 21) return 'Poor deal';
  return 'Horrible deal';
}

export default function SessionDetailPage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const chatEndRef = useRef(null);

  const [session, setSession] = useState(null);
  const [listings, setListings] = useState([]);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);

  // Add listing form state
  const [showAddForm, setShowAddForm] = useState(false);
  const [newListing, setNewListing] = useState({
    title: '',
    url: '',
    price: '',
    currency: 'USD',
    marketplace: '',
    metadata: {}
  });

  // Chat state
  const [messageText, setMessageText] = useState('');
  const [sending, setSending] = useState(false);

  useEffect(() => {
    loadSessionState();
    const interval = setInterval(loadSessionState, 3000); // Poll every 3s
    return () => clearInterval(interval);
  }, [sessionId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadSessionState = async () => {
    try {
      const response = await sessionsAPI.getState(sessionId);
      setSession(response.data.session);
      setListings(response.data.listings);
      setMessages(response.data.messages);
    } catch (error) {
      console.error('Failed to load session state:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddListing = async (e) => {
    e.preventDefault();
    try {
      await listingsAPI.create(sessionId, {
        ...newListing,
        price: newListing.price ? parseFloat(newListing.price) : null,
      });
      setNewListing({ title: '', url: '', price: '', currency: 'USD', marketplace: '', metadata: {} });
      setShowAddForm(false);
      loadSessionState();
    } catch (error) {
      console.error('Failed to add listing:', error);
    }
  };

  const handleRemoveListing = async (listingId) => {
    try {
      await listingsAPI.markRemoved(sessionId, listingId);
      loadSessionState();
    } catch (error) {
      console.error('Failed to remove listing:', error);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!messageText.trim()) return;

    setSending(true);
    try {
      await messagesAPI.send(sessionId, messageText);
      setMessageText('');
      loadSessionState();
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setSending(false);
    }
  };

  if (loading) return <div className="loading">Loading session...</div>;
  if (!session) return <div className="error">Session not found</div>;

  return (
    <div className="session-detail-page">
      <header className="page-header">
        <button onClick={() => navigate('/sessions')} className="btn-back">← Back</button>
        <div>
          <h1>{session.title}</h1>
          <p className="session-category">{session.category}</p>
        </div>
      </header>

      <div className="session-content">
        {/* Listings Section */}
        <div className="listings-section">
          <div className="section-header">
            <h2>Listings ({listings.length})</h2>
            <button onClick={() => setShowAddForm(!showAddForm)} className="btn-primary">
              {showAddForm ? 'Cancel' : '+ Add Listing'}
            </button>
          </div>

          {showAddForm && (
            <form onSubmit={handleAddListing} className="add-listing-form">
              <input
                type="text"
                placeholder="Title *"
                value={newListing.title}
                onChange={(e) => setNewListing({ ...newListing, title: e.target.value })}
                required
              />
              <input
                type="url"
                placeholder="URL"
                value={newListing.url}
                onChange={(e) => setNewListing({ ...newListing, url: e.target.value })}
              />
              <div className="price-group">
                <input
                  type="number"
                  placeholder="Price"
                  value={newListing.price}
                  onChange={(e) => setNewListing({ ...newListing, price: e.target.value })}
                />
                <select value={newListing.currency} onChange={(e) => setNewListing({ ...newListing, currency: e.target.value })}>
                  <option value="USD">USD</option>
                  <option value="EUR">EUR</option>
                  <option value="GBP">GBP</option>
                </select>
              </div>
              <input
                type="text"
                placeholder="Marketplace (e.g., Craigslist, eBay)"
                value={newListing.marketplace}
                onChange={(e) => setNewListing({ ...newListing, marketplace: e.target.value })}
              />
              <button type="submit" className="btn-primary">Add Listing</button>
            </form>
          )}

          <div className="listings-grid">
            {listings.length === 0 ? (
              <p className="empty-state">No listings yet. Add some to get started!</p>
            ) : (
              listings.map((listing) => (
                <div key={listing.id} className={`listing-card ${listing.score ? 'evaluated' : 'pending'}`}>
                  <div className="listing-header">
                    <h3>{listing.title}</h3>
                    {listing.score !== null && (
                      <span className={`deal-badge score-${Math.floor(listing.score / 20)}`}>
                        {getDealLabel(listing.score)}
                      </span>
                    )}
                  </div>

                  {listing.price && (
                    <p className="listing-price">
                      {listing.currency || '$'}{listing.price}
                    </p>
                  )}

                  {listing.url && (
                    <a href={listing.url} target="_blank" rel="noopener noreferrer" className="listing-url">
                      View listing →
                    </a>
                  )}

                  {listing.marketplace && (
                    <p className="listing-marketplace">{listing.marketplace}</p>
                  )}

                  {listing.score !== null && (
                    <div className="listing-evaluation">
                      <div className="score-bar">
                        <div className="score-fill" style={{ width: `${listing.score}%` }}></div>
                        <span className="score-value">{listing.score}/100</span>
                      </div>
                      <p className="rationale">{listing.rationale}</p>
                    </div>
                  )}

                  <button onClick={() => handleRemoveListing(listing.id)} className="btn-remove">
                    Remove
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Chat Section */}
        <div className="chat-section">
          <h2>Chat with Agent</h2>

          {session.status === 'WAITING_FOR_CLARIFICATION' && (
            <div className="clarification-notice">
              ⚠️ The agent is waiting for your answer to continue
            </div>
          )}

          <div className="messages-container">
            {messages.map((message) => (
              <div key={message.id} className={`message ${message.sender}`}>
                <div className="message-sender">{message.sender === 'user' ? 'You' : 'Agent'}</div>
                <div className="message-text">{message.text}</div>
                {message.type === 'clarification_question' && message.is_blocking && (
                  <div className="question-badge">Clarifying Question</div>
                )}
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>

          <form onSubmit={handleSendMessage} className="message-form">
            <input
              type="text"
              placeholder={session.status === 'WAITING_FOR_CLARIFICATION' ? 'Answer the question...' : 'Ask the agent about these listings...'}
              value={messageText}
              onChange={(e) => setMessageText(e.target.value)}
              disabled={sending}
            />
            <button type="submit" disabled={sending || !messageText.trim()} className="btn-primary">
              {sending ? 'Sending...' : 'Send'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
