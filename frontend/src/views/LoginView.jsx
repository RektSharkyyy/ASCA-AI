import { useState } from 'react';
import { useAuth } from '../auth/AuthContext';

export default function LoginView() {
  const { login, loading, error } = useAuth();
  const [email,    setEmail]    = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [localErr, setLocalErr] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalErr('');
    if (!email.trim() || !password.trim()) {
      setLocalErr('Please enter your email and password.');
      return;
    }
    const result = await login(email.trim(), password);
    if (!result.success) setLocalErr(result.error || 'Login failed.');
  };

  const displayError = localErr || error;

  return (
    <div className="login-page">
      {/* Animated background blobs */}
      <div className="login-blob login-blob-1" />
      <div className="login-blob login-blob-2" />
      <div className="login-blob login-blob-3" />

      <div className="login-card">
        {/* Logo */}
        <div className="login-logo">
          <div className="login-logo-icon">🌾</div>
          <div>
            <div className="login-logo-title">ASCA AI</div>
            <div className="login-logo-sub">Agricultural Supply Chain Advisory</div>
          </div>
        </div>

        {/* Tagline */}
        <div className="login-tagline">
          <p>Multi-agent market intelligence for Sri Lanka's economic centres.</p>
        </div>

        {/* Feature badges */}
        <div className="login-badges">
          {['📈 Prophet Forecasting', '🤝 B2B Matching', '⚠️ Surplus Alerts', '🌐 Live Web Search'].map((b, i) => (
            <span key={i} className="login-badge">{b}</span>
          ))}
        </div>

        {/* Form */}
        <form className="login-form" onSubmit={handleSubmit} autoComplete="on">
          <div className="login-form-group">
            <label className="login-label" htmlFor="login-email">Email Address</label>
            <div className="login-input-wrap">
              <span className="login-input-icon">✉️</span>
              <input
                id="login-email"
                type="email"
                className="login-input"
                placeholder="you@example.com"
                value={email}
                onChange={e => setEmail(e.target.value)}
                autoComplete="email"
                required
              />
            </div>
          </div>

          <div className="login-form-group">
            <label className="login-label" htmlFor="login-password">Password</label>
            <div className="login-input-wrap">
              <span className="login-input-icon">🔒</span>
              <input
                id="login-password"
                type={showPass ? 'text' : 'password'}
                className="login-input"
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
              <button
                type="button"
                className="login-show-pass"
                onClick={() => setShowPass(v => !v)}
                tabIndex={-1}
                aria-label="Toggle password visibility"
              >
                {showPass ? '🙈' : '👁️'}
              </button>
            </div>
          </div>

          {displayError && (
            <div className="login-error" role="alert">
              ⚠️ {displayError}
            </div>
          )}

          <button
            type="submit"
            className={`login-btn ${loading ? 'loading' : ''}`}
            disabled={loading}
          >
            {loading ? (
              <span className="login-btn-spinner">
                <span className="thinking-dot" />
                <span className="thinking-dot" />
                <span className="thinking-dot" />
              </span>
            ) : '🚀 Sign In to ASCA AI'}
          </button>
        </form>

        {/* Footer */}
        <div className="login-footer">
          Dambulla &amp; Thambuththegama Economic Centres
          <br />
          <span style={{ color: 'var(--text-muted)', fontSize: 10 }}>
            Powered by Multi-Agent AI · Prophet · ChromaDB · FastAPI
          </span>
        </div>
      </div>
    </div>
  );
}
