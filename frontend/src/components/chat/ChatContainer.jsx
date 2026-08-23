import { useState, useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';
import { postChat } from '../../api/client';

const now = () => new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });

const INITIAL_MESSAGES = [
  {
    id: 1,
    role: 'agent',
    time: '—',
    text: 'Good evening! I am ASCA AI — your Agricultural Supply Chain Advisory Intelligence. I am currently monitoring Dambulla and Thambuththegama Economic Centres.\n\nI can help you with:\n• 14-day crop price forecasting (Prophet + LSTM)\n• Surplus anomaly detection & alerts\n• B2B buyer matching via FEFO risk engine\n• Executive blueprint generation\n\nHow may I assist you today?',
    thoughts: null,
    actions: null,
  },
];

export default function ChatContainer({ activeCenter, onArtifact }) {
  const [messages, setMessages] = useState(INITIAL_MESSAGES);
  const [thinking, setThinking]   = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const bottomRef                 = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, thinking]);

  const handleSend = async (text) => {
    const userMsg = { id: Date.now(), role: 'user', time: now(), text };
    setMessages(m => [...m, userMsg]);
    setThinking(true);

    try {
      const data = await postChat(text, activeCenter, sessionId);

      // Persist session ID for conversation continuity
      if (data.session_id && !sessionId) setSessionId(data.session_id);

      // Map backend ChatResponse → MessageBubble-compatible shape
      const agentMsg = {
        id:      Date.now() + 1,
        role:    'agent',
        time:    now(),
        text:    data.answer,
        thoughts: data.thoughts?.length
          ? data.thoughts.map(t => ({ tool: t.tool, detail: ' ' + t.detail }))
          : null,
        actions: data.actions?.length
          ? data.actions.map(a => ({
              label:   a.label,
              icon:    a.icon,
              primary: a.primary,
              prompt:  a.prompt,
            }))
          : null,
        sources: data.sources ?? [],
      };

      setMessages(m => [...m, agentMsg]);

      // Trigger the right-panel chart when the backend attaches one
      if (data.chart) {
        onArtifact({
          type:   'chart',
          crop:   data.chart.crop,
          data:   data.chart.data,
        });
      }
    } catch (err) {
      const errMsg = {
        id:   Date.now() + 1,
        role: 'agent',
        time: now(),
        text: `⚠️ Could not reach the ASCA AI backend. Please make sure the server is running.\n\n_Error: ${err.message}_`,
        thoughts: null,
        actions: null,
      };
      setMessages(m => [...m, errMsg]);
    } finally {
      setThinking(false);
    }
  };

  // Allow inline action buttons to re-send their prompt
  const handleAction = (action) => {
    if (action.prompt) handleSend(action.prompt);
  };

  return (
    <div className="chat-view">
      <div className="chat-messages">
        {messages.length === 1 && !thinking && (
          <div className="chat-welcome">
            <div className="chat-welcome-icon">🌾</div>
            <h2>ASCA AI Advisory Intelligence</h2>
            <p>Sri Lanka Agricultural Supply Chain — Dambulla &amp; Thambuththegama Economic Centres. Ask me about crop price forecasts, surplus detection, and B2B buyer matching.</p>
            <div className="quick-chips">
              {['📈 Tomato price forecast', '🤝 Match B2B buyers', '⚠️ Detect today\'s anomalies', '📄 Generate Blueprint'].map((c, i) => (
                <button key={i} className="quick-chip" onClick={() => handleSend(c)}>{c}</button>
              ))}
            </div>
          </div>
        )}
        {messages.map(m => (
          <MessageBubble key={m.id} msg={m} onAction={handleAction} />
        ))}
        {thinking && (
          <div className="message-row agent fade-in">
            <div className="message-avatar agent">🌾</div>
            <div className="message-content">
              <div className="message-meta">ASCA AI · Processing…</div>
              <div className="message-bubble agent">
                <div className="thinking-dots">
                  <div className="thinking-dot" />
                  <div className="thinking-dot" />
                  <div className="thinking-dot" />
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <ChatInput onSend={handleSend} disabled={thinking} />
    </div>
  );
}
