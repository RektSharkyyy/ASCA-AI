import { useState, useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';
import { postChat, getChatSessionMessages } from '../../api/client';

const now = () => new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });

const WELCOME_MSG = {
  id: '__welcome__',
  role: 'agent',
  time: '—',
  text: 'Good evening! I am ASCA AI — your Agricultural Supply Chain Advisory Intelligence. I am currently monitoring Dambulla and Thambuththegama Economic Centres.\n\nI can help you with:\n• 14-day crop price forecasting (Prophet + LSTM)\n• Surplus anomaly detection & alerts\n• B2B buyer matching via FEFO risk engine\n• Executive blueprint generation\n\nHow may I assist you today?',
  thoughts: null,
  actions: null,
};

export default function ChatContainer({
  activeCenter,
  onArtifact,
  activeSessionId,    // null = new chat; string = load this session
  onSessionUpdated,   // called after every new exchange → triggers sidebar refresh
  onNewSession,       // called when user explicitly wants a new chat
}) {
  const [messages,  setMessages]  = useState([WELCOME_MSG]);
  const [thinking,  setThinking]  = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const bottomRef                 = useRef(null);

  // Auto-scroll on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, thinking]);

  // When activeSessionId changes (sidebar click or new session), load or reset
  useEffect(() => {
    if (!activeSessionId) {
      // New / fresh chat
      setMessages([WELCOME_MSG]);
      setSessionId(null);
      return;
    }

    if (activeSessionId === sessionId) return;  // already loaded

    // Load the past session thread
    setThinking(true);
    getChatSessionMessages(activeSessionId)
      .then(items => {
        const msgs = [];
        items.forEach(item => {
          const t = new Date(item.created_at).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
          msgs.push({ id: `u-${item.id}`, role: 'user',  time: t, text: item.query  });
          msgs.push({ id: `a-${item.id}`, role: 'agent', time: t, text: item.answer });
        });
        setMessages(msgs.length ? msgs : [WELCOME_MSG]);
        setSessionId(activeSessionId);
      })
      .catch(() => {
        setMessages([WELCOME_MSG]);
        setSessionId(null);
      })
      .finally(() => setThinking(false));
  }, [activeSessionId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Send a message
  const handleSend = async (text) => {
    const userMsg = { id: Date.now(), role: 'user', time: now(), text };
    setMessages(m => [...m, userMsg]);
    setThinking(true);

    try {
      const data = await postChat(text, activeCenter, sessionId);

      // Persist session continuity
      if (data.session_id && !sessionId) setSessionId(data.session_id);

      const agentMsg = {
        id:      Date.now() + 1,
        role:    'agent',
        time:    now(),
        text:    data.answer,
        thoughts: data.thoughts?.length
          ? data.thoughts.map(t => ({ tool: t.tool, detail: ' ' + t.detail }))
          : null,
        actions: data.actions?.length
          ? data.actions.map(a => ({ label: a.label, icon: a.icon, primary: a.primary, prompt: a.prompt }))
          : null,
        sources: data.sources ?? [],
      };

      setMessages(m => [...m, agentMsg]);

      if (data.chart) {
        onArtifact?.({ type: 'chart', crop: data.chart.crop, data: data.chart.data });
      }

      // Notify App.jsx so Sidebar refreshes Recent Sessions
      onSessionUpdated?.();

    } catch (err) {
      setMessages(m => [...m, {
        id:   Date.now() + 1,
        role: 'agent',
        time: now(),
        text: `⚠️ Could not reach the ASCA AI backend.\n\n_Error: ${err.message}_`,
        thoughts: null,
        actions: null,
      }]);
    } finally {
      setThinking(false);
    }
  };

  const handleAction = (action) => {
    if (action.prompt) handleSend(action.prompt);
  };

  const isWelcome = messages.length === 1 && messages[0].id === '__welcome__';

  return (
    <div className="chat-view">
      <div className="chat-messages">
        {isWelcome && !thinking && (
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
