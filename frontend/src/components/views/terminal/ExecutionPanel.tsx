import React, { useState } from 'react';
import { Zap, Target, X } from 'lucide-react';
import { useTerminalStore } from '../../../stores/terminalStore';
import { submitManualOrder, closePosition, setBreakeven } from '../../../services/api';
import type { Position } from '../../../types/market';

interface ExecutionPanelProps {
  positions: Position[];
}

export const ExecutionPanel: React.FC<ExecutionPanelProps> = ({ positions }) => {
  const { activeSymbol, orderSide, setOrderSide, riskPct, setRiskPct } = useTerminalStore();
  const [symInput, setSymInput] = useState(`${activeSymbol}USDT`);
  const [execMode, setExecMode] = useState<'POST_ONLY' | 'LIMIT_CHASE' | 'MARKET'>('POST_ONLY');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');

  const handleOrder = async () => {
    setIsSubmitting(true);
    setStatusMsg(`Submitting ${execMode} ${orderSide} order...`);
    try {
      const res = await submitManualOrder(symInput, orderSide, riskPct, execMode);
      if (res.success || res.status === 'OK') {
        const feeSavingsNote = res.is_maker || execMode === 'POST_ONLY' ? ' [Maker Fee: 0.02%]' : ' [Taker Fee: 0.05%]';
        setStatusMsg(`✅ Order executed!${feeSavingsNote}`);
      } else {
        setStatusMsg(`⚠️ ${res.message || res.error || 'Submitted'}`);
      }
    } catch (e: any) {
      setStatusMsg(`❌ Error: ${e.message}`);
    } finally {
      setIsSubmitting(false);
      setTimeout(() => setStatusMsg(''), 5000);
    }
  };

  const handleClose = async (sym: string) => {
    if (!window.confirm(`Close position ${sym}?`)) return;
    try {
      await closePosition(sym);
    } catch (e) {
      console.error(e);
    }
  };

  const handleBreakeven = async (sym: string) => {
    try {
      await setBreakeven(sym);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <aside style={{
      width: '320px',
      background: 'var(--bg-surface)',
      display: 'flex',
      flexDirection: 'column',
      flexShrink: 0,
      overflow: 'hidden'
    }}>
      {/* Header */}
      <div style={{
        padding: '10px 14px',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)' }}>
          Execution & Positions
        </span>
        <span className="status-pill blue" style={{ fontSize: '9px' }}>
          {positions.length} ACTIVE
        </span>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '12px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {/* Order Entry Widget */}
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '12px',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-primary)' }}>
              Binance Futures (20x)
            </span>
            <span className="status-pill green" style={{ fontSize: '8px', padding: '1px 5px' }}>
              TESTNET DEMO
            </span>
          </div>

          {/* Execution Mode Selector (Post-Only GTX vs Limit-Chase vs Market) */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '10.5px', color: 'var(--text-secondary)' }}>Execution Type</span>
              <span style={{
                fontSize: '8.5px',
                padding: '1px 6px',
                borderRadius: '100px',
                background: execMode === 'POST_ONLY' ? 'rgba(0, 240, 255, 0.12)' : 'rgba(255, 255, 255, 0.05)',
                color: execMode === 'POST_ONLY' ? 'var(--color-cyan)' : 'var(--text-muted)',
                border: `1px solid ${execMode === 'POST_ONLY' ? 'var(--color-cyan)' : 'var(--border-subtle)'}`,
                fontWeight: 700
              }}>
                {execMode === 'POST_ONLY' ? 'MAKER: 0.02% (HEMAT 60%)' : 'TAKER: 0.05%'}
              </span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '6px' }}>
              <button
                type="button"
                className="btn btn-sm"
                onClick={() => setExecMode('POST_ONLY')}
                style={{
                  background: execMode === 'POST_ONLY' ? 'rgba(0, 240, 255, 0.12)' : 'transparent',
                  borderColor: execMode === 'POST_ONLY' ? 'var(--color-cyan)' : 'var(--border-subtle)',
                  color: execMode === 'POST_ONLY' ? 'var(--color-cyan)' : 'var(--text-secondary)',
                  fontSize: '10px',
                  padding: '5px 6px',
                  fontWeight: 600
                }}
              >
                ⚡ Post-Only (GTX)
              </button>
              <button
                type="button"
                className="btn btn-sm"
                onClick={() => setExecMode('LIMIT_CHASE')}
                style={{
                  background: execMode === 'LIMIT_CHASE' ? 'rgba(255, 255, 255, 0.08)' : 'transparent',
                  borderColor: execMode === 'LIMIT_CHASE' ? 'var(--color-yellow)' : 'var(--border-subtle)',
                  color: execMode === 'LIMIT_CHASE' ? 'var(--color-yellow)' : 'var(--text-secondary)',
                  fontSize: '10px',
                  padding: '5px 6px',
                  fontWeight: 600
                }}
              >
                Limit-Chase
              </button>
            </div>
          </div>

          {/* Side Toggle */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
            <button
              className={`btn btn-sm ${orderSide === 'BUY' ? 'btn-success' : 'btn-ghost'}`}
              onClick={() => setOrderSide('BUY')}
              style={{
                background: orderSide === 'BUY' ? 'var(--color-green-dim)' : 'transparent',
                borderColor: orderSide === 'BUY' ? 'var(--color-green)' : 'var(--border-subtle)',
                color: orderSide === 'BUY' ? 'var(--color-green)' : 'var(--text-secondary)'
              }}
            >
              BUY / LONG
            </button>
            <button
              className={`btn btn-sm ${orderSide === 'SELL' ? 'btn-danger' : 'btn-ghost'}`}
              onClick={() => setOrderSide('SELL')}
              style={{
                background: orderSide === 'SELL' ? 'var(--color-red-dim)' : 'transparent',
                borderColor: orderSide === 'SELL' ? 'var(--color-red)' : 'var(--border-subtle)',
                color: orderSide === 'SELL' ? 'var(--color-red)' : 'var(--text-secondary)'
              }}
            >
              SELL / SHORT
            </button>
          </div>

          {/* Risk Allocation Slider */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10.5px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Risk Allocation (% Equity)</span>
              <span className="mono" style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{riskPct}%</span>
            </div>
            <input
              type="range"
              min="0.5"
              max="5.0"
              step="0.25"
              value={riskPct}
              onChange={(e) => setRiskPct(parseFloat(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--color-blue)' }}
            />
          </div>

          {/* Target Symbol */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <span style={{ fontSize: '10.5px', color: 'var(--text-secondary)' }}>Target Symbol</span>
            <input
              type="text"
              value={symInput}
              onChange={(e) => setSymInput(e.target.value.toUpperCase())}
              style={{
                background: 'var(--bg-surface)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '6px 10px',
                color: 'var(--text-primary)',
                fontFamily: 'var(--font-mono)',
                fontSize: '11.5px',
                outline: 'none'
              }}
            />
          </div>

          {/* Execute Button */}
          <button
            className="btn btn-primary"
            onClick={handleOrder}
            disabled={isSubmitting}
            style={{ width: '100%', padding: '8px', fontWeight: 700 }}
          >
            <Zap size={13} />
            <span>{isSubmitting ? 'Executing...' : 'Execute Smart Order'}</span>
          </button>

          {statusMsg && (
            <div style={{ fontSize: '10.5px', textAlign: 'center', color: 'var(--color-cyan)', marginTop: '2px' }}>
              {statusMsg}
            </div>
          )}
        </div>

        {/* Active Positions List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>
            Active Positions
          </span>

          {positions.length === 0 ? (
            <div style={{
              background: 'var(--bg-card)',
              border: '1px dashed var(--border-light)',
              borderRadius: 'var(--radius-md)',
              padding: '24px 14px',
              textAlign: 'center',
              color: 'var(--text-muted)',
              fontSize: '11.5px'
            }}>
              No active positions open. Autopilot scanning for high-confluence setups.
            </div>
          ) : (
            positions.map((p, idx) => {
              const isLong = (p.side || '').toUpperCase() === 'LONG' || (p.side || '').toUpperCase() === 'BUY';
              const pnl = p.unrealized_pnl ?? p.pnl_usd ?? p.pnl ?? 0;
              const pnlColor = pnl >= 0 ? 'var(--color-green)' : 'var(--color-red)';
              const pnlSign = pnl >= 0 ? '+' : '';

              return (
                <div
                  key={idx}
                  style={{
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-md)',
                    padding: '10px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ fontWeight: 800, fontSize: '12px', color: 'var(--text-primary)' }}>
                        {p.symbol}
                      </span>
                      <span className={`status-pill ${isLong ? 'green' : 'red'}`} style={{ fontSize: '8.5px', padding: '1px 5px' }}>
                        {p.side} {p.leverage || 20}x
                      </span>
                    </div>
                    <span className="mono" style={{ fontSize: '13px', fontWeight: 800, color: pnlColor }}>
                      {pnlSign}${pnl.toFixed(2)}
                    </span>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px' }} className="mono">
                    <div className="pos-metric-item">
                      <span className="pos-metric-key">Entry Price</span>
                      <span className="pos-metric-val">${(p.entry_price || 0).toLocaleString()}</span>
                    </div>
                    <div className="pos-metric-item">
                      <span className="pos-metric-key">Mark Price</span>
                      <span className="pos-metric-val">${(p.mark_price || 0).toLocaleString()}</span>
                    </div>
                    <div className="pos-metric-item">
                      <span className="pos-metric-key">Stop Loss</span>
                      <span className="pos-metric-val" style={{ color: 'var(--color-red)' }}>${(p.sl || 0).toLocaleString()}</span>
                    </div>
                    <div className="pos-metric-item">
                      <span className="pos-metric-key">Take Profit</span>
                      <span className="pos-metric-val" style={{ color: 'var(--color-green)' }}>${(p.tp || 0).toLocaleString()}</span>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '6px', marginTop: '2px' }}>
                    <button
                      className="btn btn-ghost btn-sm"
                      onClick={() => handleBreakeven(p.symbol)}
                      style={{ flex: 1 }}
                    >
                      <Target size={11} />
                      <span>Breakeven</span>
                    </button>
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={() => handleClose(p.symbol)}
                      style={{ flex: 1 }}
                    >
                      <X size={11} />
                      <span>Close</span>
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </aside>
  );
};
