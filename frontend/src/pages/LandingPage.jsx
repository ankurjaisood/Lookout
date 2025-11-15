import React from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/LandingPage.css';

const LandingPage = () => {
  const navigate = useNavigate();

  return (
    <div className="landing-page">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <div className="hero-badge">AI-Powered Marketplace Research</div>
          <h1 className="hero-title">
            Find the Best Deals with
            <span className="gradient-text"> Lookout</span>
          </h1>
          <p className="hero-subtitle">
            Your intelligent agent for evaluating online marketplace listings.
            Get instant deal quality scores and personalized insights for cars, electronics, and more.
          </p>
          <div className="hero-buttons">
            <button className="btn-hero-primary" onClick={() => navigate('/signup')}>
              Get Started Free
            </button>
            <button className="btn-hero-secondary" onClick={() => navigate('/login')}>
              Sign In
            </button>
          </div>
          <div className="hero-stats">
            <div className="stat">
              <div className="stat-value">AI-Powered</div>
              <div className="stat-label">Gemini 1.5</div>
            </div>
            <div className="stat">
              <div className="stat-value">Instant</div>
              <div className="stat-label">Evaluation</div>
            </div>
            <div className="stat">
              <div className="stat-value">Smart</div>
              <div className="stat-label">Insights</div>
            </div>
          </div>
        </div>
        <div className="hero-visual">
          <div className="floating-card card-1">
            <div className="deal-badge-demo great">GREAT DEAL</div>
            <div className="card-content">Score: 92/100</div>
          </div>
          <div className="floating-card card-2">
            <div className="deal-badge-demo good">GOOD DEAL</div>
            <div className="card-content">Score: 75/100</div>
          </div>
          <div className="floating-card card-3">
            <div className="deal-badge-demo fair">FAIR DEAL</div>
            <div className="card-content">Score: 58/100</div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <div className="section-header-center">
          <h2 className="section-title">How Lookout Works</h2>
          <p className="section-subtitle">Three simple steps to smarter shopping decisions</p>
        </div>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">📝</div>
            <h3>1. Add Listings</h3>
            <p>Paste URLs or descriptions from any marketplace - eBay, Craigslist, Facebook Marketplace, AutoTrader, and more.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🤖</div>
            <h3>2. AI Analysis</h3>
            <p>Our Gemini-powered agent evaluates each listing based on price, condition, features, and market data.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">⭐</div>
            <h3>3. Get Insights</h3>
            <p>Receive detailed scores (0-100) with explanations, ranked from horrible to great deals.</p>
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="benefits-section">
        <div className="section-header-center">
          <h2 className="section-title">Why Choose Lookout?</h2>
          <p className="section-subtitle">Intelligent features that save you time and money</p>
        </div>
        <div className="benefits-grid">
          <div className="benefit-item">
            <div className="benefit-icon">💬</div>
            <div className="benefit-content">
              <h4>Interactive Chat</h4>
              <p>Chat with the AI agent to refine your search criteria and get clarifications</p>
            </div>
          </div>
          <div className="benefit-item">
            <div className="benefit-icon">🎯</div>
            <div className="benefit-content">
              <h4>Personalized Preferences</h4>
              <p>Lookout learns your preferences over time for more accurate evaluations</p>
            </div>
          </div>
          <div className="benefit-item">
            <div className="benefit-icon">📊</div>
            <div className="benefit-content">
              <h4>Deal Quality Scores</h4>
              <p>Clear 0-100 scores with detailed rationales for every listing</p>
            </div>
          </div>
          <div className="benefit-item">
            <div className="benefit-icon">❓</div>
            <div className="benefit-content">
              <h4>Smart Questions</h4>
              <p>Agent asks clarifying questions inline to get missing details</p>
            </div>
          </div>
          <div className="benefit-item">
            <div className="benefit-icon">🔄</div>
            <div className="benefit-content">
              <h4>Re-evaluate Anytime</h4>
              <p>Update listings and get fresh evaluations with one click</p>
            </div>
          </div>
          <div className="benefit-item">
            <div className="benefit-icon">📝</div>
            <div className="benefit-content">
              <h4>Session Requirements</h4>
              <p>Set your budget, must-haves, and deal-breakers per session</p>
            </div>
          </div>
        </div>
      </section>

      {/* Categories Section */}
      <section className="categories-section">
        <div className="section-header-center">
          <h2 className="section-title">Perfect For Multiple Categories</h2>
          <p className="section-subtitle">Research any type of marketplace listing</p>
        </div>
        <div className="categories-grid">
          <div className="category-card">
            <div className="category-emoji">🚗</div>
            <h3>Cars & Vehicles</h3>
            <p>Used cars, motorcycles, trucks, RVs</p>
          </div>
          <div className="category-card">
            <div className="category-emoji">💻</div>
            <h3>Electronics</h3>
            <p>Laptops, phones, cameras, gaming</p>
          </div>
          <div className="category-card">
            <div className="category-emoji">🏠</div>
            <h3>Home & Furniture</h3>
            <p>Appliances, furniture, decor</p>
          </div>
          <div className="category-card">
            <div className="category-emoji">🎸</div>
            <h3>Hobbies</h3>
            <p>Musical instruments, collectibles, sports</p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="cta-content">
          <h2>Ready to Find Amazing Deals?</h2>
          <p>Join Lookout today and never overpay again</p>
          <button className="btn-cta" onClick={() => navigate('/signup')}>
            Start Evaluating Listings
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="footer-content">
          <div className="footer-brand">
            <h3>Lookout</h3>
            <p>AI-powered marketplace research agent</p>
          </div>
          <div className="footer-links">
            <div className="footer-section">
              <h4>Product</h4>
              <a onClick={() => navigate('/signup')}>Get Started</a>
              <a onClick={() => navigate('/login')}>Sign In</a>
            </div>
            <div className="footer-section">
              <h4>Technology</h4>
              <p className="footer-tech">Powered by Google Gemini AI</p>
              <p className="footer-tech">Built with React & FastAPI</p>
            </div>
          </div>
        </div>
        <div className="footer-bottom">
          <p>&copy; 2025 Lookout. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
