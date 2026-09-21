import React, { useState } from 'react';
import { X, Bot, Send } from 'lucide-react';
import { useTerminalStore } from '../../stores/terminalStore';
import { queryAiOfficer } from '../../services/api';

export const AiOfficerModal: React.FC = () => {
  const { aiModalOpen, setAiModalOpen } = useTerminalStore();
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  if (!aiModalOpen) return null;

  const handleSend = async (customQuery?: string) => {
    const q = (customQuery || query).trim();
    if (!q) return;
    setIsLoading(true);
    setResponse('Consulting AI Senior Quant Officer & Local Reflex Engine...');
    try {
      const res = await queryAiOfficer(q);
      setResponse(res.answer || res.response || JSON.stringify(res, null, 2));
    } catch (e: any) {
      setResponse(`⚠️ Error: ${e.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 300,
      padding: '20px'
    }}>
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-light)',
        borderRadius: 'var(--radius-lg)',
        width: '100%',
        maxWidth: '600px',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        {/* Modal Header */}
        <div style={{
          padding: '12px 16px',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Bot size={16} color="var(--color-purple)" />
            <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--color-purple)' }}>
              AI Senior Quant Officer Co-Pilot
            </span>
            <span className="status-pill purple" style={{ fontSize: '8.5px' }}>ONLINE</span>
          </div>
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => setAiModalOpen(false)}
          >
            <X size={14} />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              type="text"
              placeholder="Ask AI about market confluence, portfolio risk, or active setups..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              style={{
                flex: 1,
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '8px 12px',
                color: 'var(--text-primary)',
                fontSize: '12px',
                outline: 'none'
              }}
            />
            <button
              className="btn btn-primary btn-sm"
              onClick={() => handleSend()}
              disabled={isLoading}
            >
              <Send size={12} />
              <span>Ask</span>
            </button>
          </div>

          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => {
                const q = 'Evaluate active positions and current portfolio risk';
                setQuery(q);
                handleSend(q);
              }}
            >
              🛡️ Position Risk Audit
            </button>
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => {
                const q = 'What is the current macro liquidity regime and news shield status?';
                setQuery(q);
                handleSend(q);
              }}
            >
              📰 Macro News Status
            </button>
          </div>

          <div style={{
            background: 'var(--bg-canvas)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '14px',
            minHeight: '140px',
            fontSize: '12px',
            lineHeight: 1.6,
            color: 'var(--text-primary)'
          }}>
            {response || 'Type a query above or click a prompt to consult the AI Senior Quant Officer.'}
          </div>
        </div>
      </div>
    </div>
  );
};
