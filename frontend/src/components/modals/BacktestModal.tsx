import React, { useState } from 'react';
import { X, FlaskConical } from 'lucide-react';
import { useTerminalStore } from '../../stores/terminalStore';

export const BacktestModal: React.FC = () => {
  const { backtestModalOpen, setBacktestModalOpen } = useTerminalStore();
  const [symbol, setSymbol] = useState('BTC');
  const [isRunning, setIsRunning] = useState(false);
  const [results, setResults] = useState<any>(null);

  if (!backtestModalOpen) return null;

  const handleRun = async () => {
    setIsRunning(true);
    try {
      const res = await fetch(`/api/backtest?symbol=${symbol}&bar=1H&candles=300`).then((r) => r.json());
      setResults(res);
    } catch (e: any) {
      setResults({ error: e.message });
    } finally {
      setIsRunning(false);
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
        maxWidth: '560px',
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
            <FlaskConical size={16} color="var(--color-blue)" />
            <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)' }}>
              Quantitative Strategy Flight Simulator
            </span>
          </div>
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => setBacktestModalOpen(false)}
          >
            <X size={14} />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Select Asset:</span>
            <select
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              style={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '6px 12px',
                color: 'var(--text-primary)',
                fontFamily: 'var(--font-sans)',
                fontSize: '12px',
                outline: 'none'
              }}
            >
              <option value="BTC">BTC/USDT</option>
              <option value="ETH">ETH/USDT</option>
              <option value="SOL">SOL/USDT</option>
              <option value="LINK">LINK/USDT</option>
            </select>

            <button className="btn btn-primary btn-sm" onClick={handleRun} disabled={isRunning}>
              <span>{isRunning ? 'Simulating...' : 'Run Simulation'}</span>
            </button>
          </div>

          <div style={{
            background: 'var(--bg-canvas)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '14px',
            minHeight: '140px',
            fontSize: '11.5px',
            lineHeight: 1.6,
            color: 'var(--text-secondary)'
          }} className="mono">
            {results ? (
              <pre style={{ margin: 0, whiteSpace: 'pre-wrap', color: 'var(--text-primary)' }}>
                {JSON.stringify(results, null, 2)}
              </pre>
            ) : (
              'Select parameters and click "Run Simulation" to backtest across historical klines.'
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
