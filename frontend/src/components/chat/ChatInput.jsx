import { useState, useRef, useEffect } from 'react';
import { Send, Mic, Paperclip } from 'lucide-react';

const QUICK_CHIPS = [
  '📈 Tomato forecast – Dambulla',
  '🤝 Find B2B buyers for Beans surplus',
  '📄 Generate Executive Blueprint',
  '⚠️ Detect anomalies today',
  '💰 Dollar rate impact on imports',
];

export default function ChatInput({ onSend, disabled }) {
  const [value, setValue] = useState('');
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current) {
      ref.current.style.height = 'auto';
      ref.current.style.height = Math.min(ref.current.scrollHeight, 120) + 'px';
    }
  }, [value]);

  const send = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue('');
  };

  const onKey = e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  };

  return (
    <div className="chat-input-area">
      <div className="chat-input-chips">
        {QUICK_CHIPS.map((c, i) => (
          <button key={i} className="input-chip" onClick={() => { setValue(c.replace(/^[\S]+ /, '')); ref.current?.focus(); }}>
            {c}
          </button>
        ))}
      </div>
      <div className="chat-input-row">
        <textarea
          ref={ref}
          className="chat-input-box"
          placeholder="Ask ASCA AI about market prices, surplus detection, B2B matching…"
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={onKey}
          rows={1}
        />
        <button className="send-btn" onClick={send} disabled={!value.trim() || disabled} title="Send">
          <Send size={15} />
        </button>
      </div>
    </div>
  );
}
