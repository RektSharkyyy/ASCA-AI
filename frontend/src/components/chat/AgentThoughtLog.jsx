import { useState } from 'react';
import { ChevronDown, ChevronRight, Search, Database, Shield, Cpu, Globe } from 'lucide-react';

const STEP_ICONS = { 'Web Scraping': Globe, 'ChromaDB': Database, 'Pydantic Validation': Shield, 'Prophet Forecast': Cpu, 'Llama 3.1 8B': Cpu };

export function AgentThoughtLog({ steps }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="thought-log">
      <div className="thought-log-header" onClick={() => setOpen(o => !o)}>
        {open ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        <Cpu size={11} />
        <span>Agent Reasoning — {steps.length} steps</span>
      </div>
      {open && (
        <div className="thought-log-body">
          {steps.map((step, i) => {
            const Icon = STEP_ICONS[step.tool] || Search;
            return (
              <div key={i} className="thought-step">
                <span className="thought-step-icon"><Icon size={12} /></span>
                <span>
                  <span className="label">{step.tool}</span>
                  <span style={{ color: 'var(--text-muted)' }}>{step.detail}</span>
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
