import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { sessionsAPI, listingsAPI, messagesAPI, clarificationsAPI } from '../services/api';

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
  const previousMessageCountRef = useRef(0);

  const [session, setSession] = useState(null);
  const [listings, setListings] = useState([]);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [requirementsDraft, setRequirementsDraft] = useState('');
  const [requirementsSaving, setRequirementsSaving] = useState(false);
  const [requirementsStatus, setRequirementsStatus] = useState(null);
  const [reevaluatingListingIds, setReevaluatingListingIds] = useState(new Set());
  const [clarificationInputs, setClarificationInputs] = useState({});
  const [clarificationSubmitting, setClarificationSubmitting] = useState({});

  // Add listing form state
  const [showAddForm, setShowAddForm] = useState(false);
  const defaultListingForm = {
    title: '',
    url: '',
    price: '',
    currency: 'USD',
    marketplace: '',
    metadata: {},
    description: ''
  };

  const [newListing, setNewListing] = useState(defaultListingForm);

  const [editingListingId, setEditingListingId] = useState(null);
  const [editListingData, setEditListingData] = useState(defaultListingForm);

  // Chat state
  const [messageText, setMessageText] = useState('');
  const [sending, setSending] = useState(false);

  useEffect(() => {
    loadSessionState();
    const interval = setInterval(loadSessionState, 3000); // Poll every 3s
    return () => clearInterval(interval);
  }, [sessionId]);

  useEffect(() => {
    if (session) {
      setRequirementsDraft(session.requirements || '');
    }
  }, [session]);

  useEffect(() => {
    if (messages.length > previousMessageCountRef.current) {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
    previousMessageCountRef.current = messages.length;
  }, [messages]);

  useEffect(() => {
    const activeClarIds = new Set();
    listings.forEach((listing) => {
      (listing.clarifications || []).forEach((clarification) => {
        if (clarification.clarification_status !== 'answered') {
          activeClarIds.add(clarification.id);
        }
      });
    });

    setClarificationInputs((prev) => {
      const next = {};
      activeClarIds.forEach((id) => {
        next[id] = prev[id] || '';
      });
      return next;
    });

    setClarificationSubmitting((prev) => {
      const next = {};
      activeClarIds.forEach((id) => {
        if (prev[id]) {
          next[id] = prev[id];
        }
      });
      return next;
    });
  }, [listings]);

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
        description: newListing.description || null,
      });
      setNewListing(defaultListingForm);
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

  const handleSaveRequirements = async (e) => {
    e.preventDefault();
    setRequirementsSaving(true);
    setRequirementsStatus(null);
    try {
      const normalized = requirementsDraft.trim();
      await sessionsAPI.update(sessionId, { requirements: normalized ? normalized : null });
      setRequirementsStatus('saved');
      await loadSessionState();
    } catch (error) {
      console.error('Failed to update requirements:', error);
      setRequirementsStatus('error');
    } finally {
      setRequirementsSaving(false);
    }
  };

  const handleReevaluateListing = async (listingId) => {
    setReevaluatingListingIds((prev) => {
      const next = new Set(prev);
      next.add(listingId);
      return next;
    });
    try {
      await listingsAPI.reevaluate(sessionId, listingId);
      await loadSessionState();
    } catch (error) {
      console.error('Failed to re-evaluate listing:', error);
    } finally {
      setReevaluatingListingIds((prev) => {
        const next = new Set(prev);
        next.delete(listingId);
        return next;
      });
    }
  };

  const handleClarificationInputChange = (clarificationId, value) => {
    setClarificationInputs((prev) => ({
      ...prev,
      [clarificationId]: value,
    }));
  };

  const handleClarificationSubmit = async (clarificationId, event) => {
    event.preventDefault();
    const text = (clarificationInputs[clarificationId] || '').trim();
    if (!text) return;

    setClarificationSubmitting((prev) => ({
      ...prev,
      [clarificationId]: true,
    }));

    try {
      await clarificationsAPI.answer(sessionId, clarificationId, text);
      setClarificationInputs((prev) => ({
        ...prev,
        [clarificationId]: '',
      }));
      await loadSessionState();
    } catch (error) {
      console.error('Failed to answer clarification:', error);
    } finally {
      setClarificationSubmitting((prev) => ({
        ...prev,
        [clarificationId]: false,
      }));
    }
  };

  const handleEditListingChange = (field, value) => {
    setEditListingData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const startEditingListing = (listing) => {
    setEditingListingId(listing.id);
    setEditListingData({
      title: listing.title || '',
      url: listing.url || '',
      price: listing.price !== null && listing.price !== undefined ? String(listing.price) : '',
      currency: listing.currency || 'USD',
      marketplace: listing.marketplace || '',
      metadata: listing.listing_metadata || {},
      description: listing.description || '',
    });
  };

  const cancelEditingListing = () => {
    setEditingListingId(null);
    setEditListingData(defaultListingForm);
  };

  const handleUpdateListing = async (e) => {
    e.preventDefault();
    if (!editingListingId) return;

    try {
      await listingsAPI.update(sessionId, editingListingId, {
        ...editListingData,
        price: editListingData.price ? parseFloat(editListingData.price) : null,
        description: editListingData.description || null,
      });
      setEditingListingId(null);
      setEditListingData(defaultListingForm);
      await loadSessionState();
    } catch (error) {
      console.error('Failed to update listing:', error);
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
        <div className="requirements-section">
          <h2>Session Requirements</h2>
          <p className="requirements-hint">
            Share the must-have criteria for this search. The agent will use these when evaluating listings.
          </p>
          <form onSubmit={handleSaveRequirements} className="requirements-form">
            <textarea
              value={requirementsDraft}
              onChange={(e) => setRequirementsDraft(e.target.value)}
              placeholder="Example: Manual transmission, factory hardtop, under 50k miles, service records required."
              rows={3}
            />
            <div className="requirements-actions">
              <button type="submit" className="btn-secondary" disabled={requirementsSaving}>
                {requirementsSaving ? 'Saving...' : 'Save Requirements'}
              </button>
              {requirementsStatus === 'saved' && (
                <span className="status-badge success">Saved</span>
              )}
              {requirementsStatus === 'error' && (
                <span className="status-badge error">Failed to save</span>
              )}
            </div>
          </form>
        </div>

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
            <textarea
              placeholder="Paste the listing description/details (optional)"
              value={newListing.description}
              onChange={(e) => setNewListing({ ...newListing, description: e.target.value })}
              rows={4}
            />
            <button type="submit" className="btn-primary">Add Listing</button>
          </form>
        )}

          <div className="listings-grid">
            {listings.length === 0 ? (
              <p className="empty-state">No listings yet. Add some to get started!</p>
            ) : (
              listings.map((listing) => {
                const clarifications = listing.clarifications || [];
                return (
                  <div key={listing.id} className={`listing-card ${listing.score ? 'evaluated' : 'pending'}`}>
                    <div className="listing-header">
                      <div className="listing-title-row">
                        <h3>{listing.title}</h3>
                        <button
                          type="button"
                          className={`reevaluate-button ${reevaluatingListingIds.has(listing.id) ? 'spinning' : ''}`}
                          onClick={() => handleReevaluateListing(listing.id)}
                          disabled={reevaluatingListingIds.has(listing.id)}
                          title="Re-evaluate this listing"
                        >
                          ⟳
                        </button>
                      </div>
                      {listing.score !== null ? (
                        <span className={`deal-badge score-${Math.floor(listing.score / 20)}`}>
                          {getDealLabel(listing.score)}
                        </span>
                      ) : (
                        <span className="deal-badge pending-badge">Pending</span>
                      )}
                    </div>

                    {editingListingId === listing.id ? (
                      <form onSubmit={handleUpdateListing} className="listing-edit-form">
                        <input
                          type="text"
                          placeholder="Title"
                          value={editListingData.title}
                          onChange={(e) => handleEditListingChange('title', e.target.value)}
                          required
                        />
                        <input
                          type="url"
                          placeholder="URL"
                          value={editListingData.url}
                          onChange={(e) => handleEditListingChange('url', e.target.value)}
                        />
                        <div className="price-group">
                          <input
                            type="number"
                            placeholder="Price"
                            value={editListingData.price}
                            onChange={(e) => handleEditListingChange('price', e.target.value)}
                          />
                          <select
                            value={editListingData.currency}
                            onChange={(e) => handleEditListingChange('currency', e.target.value)}
                          >
                            <option value="USD">USD</option>
                            <option value="EUR">EUR</option>
                            <option value="GBP">GBP</option>
                          </select>
                        </div>
                        <input
                          type="text"
                          placeholder="Marketplace"
                          value={editListingData.marketplace}
                          onChange={(e) => handleEditListingChange('marketplace', e.target.value)}
                        />
                        <textarea
                          placeholder="Listing description/details"
                          value={editListingData.description}
                          onChange={(e) => handleEditListingChange('description', e.target.value)}
                          rows={4}
                        />
                        <div className="listing-edit-actions">
                          <button type="submit" className="btn-primary">Save</button>
                          <button type="button" className="btn-secondary" onClick={cancelEditingListing}>
                            Cancel
                          </button>
                        </div>
                      </form>
                    ) : (
                      <>
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

                        {listing.description && (
                          <p className="listing-description">{listing.description}</p>
                        )}
                      </>
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

                    {clarifications.length > 0 && (
                      <div className="listing-clarifications">
                        <h4>Clarifications</h4>
                        {clarifications.map((clarification) => {
                          const isAnswered = clarification.clarification_status === 'answered';
                          const inputValue = clarificationInputs[clarification.id] || '';
                          return (
                            <div
                              key={clarification.id}
                              className={`clarification-item ${isAnswered ? 'answered' : 'pending'}`}
                            >
                              <div className="clarification-question">
                                {clarification.text}
                                {clarification.is_blocking && !isAnswered && (
                                  <span className="clarification-badge">Blocking</span>
                                )}
                              </div>
                              {isAnswered ? (
                                <div className="clarification-answer">
                                  <strong>You:</strong> {clarification.answer_text || 'Answered'}
                                </div>
                              ) : (
                                <form
                                  onSubmit={(e) => handleClarificationSubmit(clarification.id, e)}
                                  className="clarification-form"
                                >
                                  <input
                                    type="text"
                                    placeholder="Type your answer..."
                                    value={inputValue}
                                    onChange={(e) => handleClarificationInputChange(clarification.id, e.target.value)}
                                  />
                                  <button
                                    type="submit"
                                    className="btn-secondary"
                                    disabled={
                                      clarificationSubmitting[clarification.id] ||
                                      !inputValue.trim()
                                    }
                                  >
                                    {clarificationSubmitting[clarification.id] ? 'Sending...' : 'Send Answer'}
                                  </button>
                                </form>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}

                    <div className="listing-actions">
                      <button
                        onClick={() => startEditingListing(listing)}
                        className="btn-secondary"
                      >
                        {editingListingId === listing.id ? 'Editing...' : 'Edit'}
                      </button>
                      <button onClick={() => handleRemoveListing(listing.id)} className="btn-remove">
                        Remove
                      </button>
                    </div>
                  </div>
                );
              })
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
