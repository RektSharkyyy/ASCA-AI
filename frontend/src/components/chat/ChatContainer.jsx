import { useState, useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';
import { FORECAST_DATA } from '../../data/mockData';

const now = () => new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });

const INITIAL_MESSAGES = [
  {
    id: 1,
    role: 'agent',
    time: '18:45',
    text: 'Good evening! I am ASCA AI — your Agricultural Supply Chain Advisory Intelligence. I am currently monitoring Dambulla and Thambuththegama Economic Centres.\n\nI can help you with:\n• 14-day crop price forecasting (Prophet + LSTM)\n• Surplus anomaly detection & alerts\n• B2B buyer matching via FEFO risk engine\n• Executive blueprint generation\n\nHow may I assist you today?',
    thoughts: null,
    actions: null,
  },
];

const buildAgentReply = (query, center) => {
  const q = query.toLowerCase();
  const cropMatch = ['tomato', 'carrot', 'beans', 'eggplant', 'cabbage', 'chilli'].find(c => q.includes(c));
  const isForecast = q.includes('forecast') || q.includes('price') || q.includes('predict');
  const isMatch    = q.includes('b2b') || q.includes('buyer') || q.includes('surplus') || q.includes('match');
  const isReport   = q.includes('report') || q.includes('blueprint') || q.includes('generate');

  const cropLabel = cropMatch ? cropMatch.charAt(0).toUpperCase() + cropMatch.slice(1) : 'Tomato';
  const chartKey  = cropLabel === 'Chilli' ? 'Green Chilli' : cropLabel;

  if (isForecast && cropMatch) {
    return {
      text: `I have run a **14-day Prophet forecast** for **${cropLabel}** at **${center === 'DAMBULLA' ? 'Dambulla' : 'Thambuththegama'} Economic Centre**.\n\n📊 Key Insights:\n• **Current price**: LKR 118/kg\n• **Day 7 forecast**: LKR 103/kg (↓12.7%)\n• **Day 14 forecast**: LKR 98/kg (↓16.9%)\n• **Surplus anomaly**: Detected — 51.08 tons above absorption capacity\n• **Risk level**: HIGH\n\nForecast chart is rendered inline below. Would you like me to match B2B buyers or generate an Executive Blueprint?`,
      thoughts: [
        { tool: 'ChromaDB', detail: ' Loaded 60-day historical price records for ' + cropLabel },
        { tool: 'Prophet Forecast', detail: ' Running 14-day projection with uncertainty bands…' },
        { tool: 'Pydantic Validation', detail: ' MarketInsight schema validated successfully' },
      ],
      chart: { data: FORECAST_DATA[chartKey] || FORECAST_DATA['Tomato'], crop: cropLabel },
      actions: [
        { label: 'Find B2B Buyers', icon: 'ext', primary: true },
        { label: 'Generate Blueprint', icon: 'pdf' },
        { label: 'Broadcast SMS Alert', icon: 'sms' },
      ],
    };
  }

  if (isMatch) {
    return {
      text: `Running **FEFO Risk Engine** against ChromaDB buyer registry for **${cropLabel} surplus at ${center === 'DAMBULLA' ? 'Dambulla' : 'Thambuththegama'}**...\n\n🤝 **2 B2B Matches Identified**:\n\n1. **Lanka Canning & Sauce Ltd** — Colombo 15\n   • Volume: 26.08 T | FEFO Score: 0.87 | Distance: 142 km\n   • Status: Active Negotiation ✅\n\n2. **Central Province Canning Mills** — Matale\n   • Volume: 25.00 T | FEFO Score: 0.67 | Distance: 28 km\n   • Status: Matched ✅\n\nTotal surplus absorbed: **51.08 T / 51.08 T (100%)**`,
      thoughts: [
        { tool: 'ChromaDB', detail: ' Vector similarity search across 12 registered buyers' },
        { tool: 'Pydantic Validation', detail: ' B2BMatchRecommendation schema validated for 2 buyers' },
        { tool: 'Llama 3.1 8B', detail: ' Synthesizing buyer recommendation narrative' },
      ],
      chart: null,
      actions: [
        { label: 'View B2B Directory', icon: 'ext', primary: true },
        { label: 'Broadcast WhatsApp Alert', icon: 'sms' },
        { label: 'Generate Blueprint PDF', icon: 'pdf' },
      ],
    };
  }

  if (isReport) {
    return {
      text: `Generating **Executive Advisory Blueprint** for the current session at **${center === 'DAMBULLA' ? 'Dambulla' : 'Thambuththegama'}**...\n\n📄 Blueprint includes:\n• Crop price forecasts (6 crops, 14-day)\n• Surplus anomaly report\n• B2B match registry (FEFO-ranked)\n• Risk level: **HIGH** — Immediate action recommended\n\nBlueprint is Pydantic-schema validated and ready for PDF export.`,
      thoughts: [
        { tool: 'Pydantic Validation', detail: ' ExecutiveAdvisoryBlueprint schema construction' },
        { tool: 'Llama 3.1 8B', detail: ' Synthesizing advisory narrative from MarketInsight + B2BMatchRecommendation' },
      ],
      chart: null,
      actions: [
        { label: 'Download PDF', icon: 'pdf', primary: true },
        { label: 'Broadcast SMS Alert', icon: 'sms' },
      ],
    };
  }

  return {
    text: `I have received your query. Let me process it using the ASCA AI pipeline:\n\n1. ✅ **Domain Guardrail** — Query is in scope (Sri Lankan agricultural supply chain)\n2. ✅ **Query Router** — Routed to RAG pipeline\n3. 🔄 **Market Scout Agent** — Fetching historical data…\n\nPlease try a more specific query like:\n• "Show tomato forecast for Dambulla"\n• "Find B2B buyers for Beans surplus"\n• "Generate this week's Executive Blueprint"`,
    thoughts: [
      { tool: 'Pydantic Validation', detail: ' Domain Guardrail: in_scope (confidence: 0.92)' },
      { tool: 'Llama 3.1 8B', detail: ' Router classified as: rag (confidence: 0.88)' },
    ],
    chart: null,
    actions: [],
  };
};

export default function ChatContainer({ activeCenter, onArtifact }) {
  const [messages, setMessages]   = useState(INITIAL_MESSAGES);
  const [thinking, setThinking]   = useState(false);
  const bottomRef                 = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, thinking]);

  const handleSend = (text) => {
    const userMsg = { id: Date.now(), role: 'user', time: now(), text };
    setMessages(m => [...m, userMsg]);
    setThinking(true);

    setTimeout(() => {
      const reply = buildAgentReply(text, activeCenter);
      const agentMsg = { id: Date.now() + 1, role: 'agent', time: now(), ...reply };
      setMessages(m => [...m, agentMsg]);
      setThinking(false);
      if (reply.chart) onArtifact({ type: 'chart', ...reply.chart });
    }, 1800 + Math.random() * 800);
  };

  return (
    <div className="chat-view">
      <div className="chat-messages">
        {messages.length === 1 && !thinking && (
          <div className="chat-welcome">
            <div className="chat-welcome-icon">🌾</div>
            <h2>ASCA AI Advisory Intelligence</h2>
            <p>Sri Lanka Agricultural Supply Chain — Dambulla & Thambuththegama Economic Centres. Ask me about crop price forecasts, surplus detection, and B2B buyer matching.</p>
            <div className="quick-chips">
              {['📈 Tomato price forecast', '🤝 Match B2B buyers', '⚠️ Detect today\'s anomalies', '📄 Generate Blueprint'].map((c, i) => (
                <button key={i} className="quick-chip" onClick={() => handleSend(c)}>{c}</button>
              ))}
            </div>
          </div>
        )}
        {messages.map(m => <MessageBubble key={m.id} msg={m} />)}
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
