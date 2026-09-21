import React, { useEffect, useState } from 'react';
import { Flame, RefreshCw, Zap, ShieldCheck } from 'lucide-react';

export const DexRadarView: React.FC = () => {
  const [tokens, setTokens] = useState<any[]>([]);
  const [whales, setWhales] = useState<any[]>([]);
  const [autoBridge, setAutoBridge] = useState(true);
  const [safeOnly, setSafeOnly] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [dexRes, whaleRes] = await Promise.all([
        fetch('/api/dex-radar').then((r) => r.json()).catch(() => ({ tokens: [] })),
        fetch('/api/whales/recent').then((r) => r.json()).catch(() => ({ swaps: [] })),
      ]);
      setTokens(dexRes.tokens || dexRes || []);
      setWhales(whaleRes.swaps || whaleRes || []);
    } catch (e) {
      console.warn('Failed to load DEX data:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 6000);
    return () => clearInterval(interval);
  }, []);

  const filteredTokens = tokens.filter((t) => {
    if (safeOnly && (t.safety_score || 0) < 75) return false;
    return true;
  });

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Banner */}
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-lg)',
        padding: '16px 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: 'var(--radius-md)',
            background: 'rgba(0, 180, 216, 0.12)',
            border: '1px solid rgba(0, 180, 216, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-cyan)'
          }}>
            <Flame size={20} />
          </div>
          <div>
            <h2 style={{ fontSize: '15px', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
              Live DEX Pump Radar & On-Chain Whale Swaps
            </h2>
            <p style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Real-time DEX token breakout scanning, safety audit scoring, and automated 20x Futures bridging.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            className={`btn btn-sm ${autoBridge ? 'btn-success' : 'btn-ghost'}`}
            onClick={() => setAutoBridge(!autoBridge)}
          >
            <Zap size={11} />
            <span>Auto-Bridge: {autoBridge ? 'ON' : 'OFF'}</span>
          </button>
          <button
            className={`btn btn-sm ${safeOnly ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setSafeOnly(!safeOnly)}
          >
            <ShieldCheck size={11} />
            <span>Safe Only (≥75)</span>
          </button>
          <button className="btn btn-ghost btn-sm" onClick={loadData} disabled={isLoading}>
            <RefreshCw size={11} className={isLoading ? 'spin-anim' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Main Grid: DEX Table (Left) + Whales (Right) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '16px' }}>
        
        {/* Left: DEX Tokens */}
        <div className="bento-card">
          <div className="bento-card-header">
            <span className="bento-card-title">
              <span>🚀 Trending DEX Breakouts</span>
              <span className="status-pill blue">AUTO-ADAPTIVE</span>
            </span>
          </div>

          <div className="data-table-wrap">
            <table className="data-table mono">
              <thead>
                <tr>
                  <th>Token</th>
                  <th>Chain</th>
                  <th>Price</th>
                  <th>5m Vol</th>
                  <th>Liquidity</th>
                  <th>Alpha</th>
                  <th>Safety</th>
                </tr>
              </thead>
              <tbody>
                {filteredTokens.length === 0 ? (
                  <tr>
                    <td colSpan={7} style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                      Streaming live DEX breakouts...
                    </td>
                  </tr>
                ) : (
                  filteredTokens.map((t, idx) => (
                    <tr key={idx}>
                      <td style={{ fontWeight: 700 }}>{t.symbol || t.token_symbol}</td>
                      <td>
                        <span className="status-pill blue" style={{ fontSize: '8px' }}>
                          {t.chain || 'SOL'}
                        </span>
                      </td>
                      <td>${(t.price || 0).toFixed(4)}</td>
                      <td>${(t.volume_5m || 0).toLocaleString()}</td>
                      <td>${(t.liquidity_usd || 0).toLocaleString()}</td>
                      <td style={{ color: 'var(--color-green)' }}>+{t.alpha_velocity || 12.4}%</td>
                      <td>
                        <span className="status-pill green" style={{ fontSize: '8.5px' }}>
                          {t.safety_score || 85}/100
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: Whale Swaps */}
        <div className="bento-card">
          <div className="bento-card-header">
            <span className="bento-card-title">
              <span>🐋 Live Whale Swaps & Inflow</span>
              <span className="status-pill purple">STREAMING</span>
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '380px', overflowY: 'auto' }}>
            {whales.length === 0 ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '11px' }}>
                Loading live whale swaps and smart money accumulations...
              </div>
            ) : (
              whales.map((w, idx) => (
                <div
                  key={idx}
                  style={{
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-sm)',
                    padding: '8px 10px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                    <span style={{ fontWeight: 700, fontSize: '11px', color: 'var(--text-primary)' }}>
                      {w.wallet_label || 'Smart Whale'}
                    </span>
                    <span style={{ fontSize: '9px', color: 'var(--text-muted)' }}>
                      {w.tx_type || 'SWAP'} {w.token_amount} {w.token_symbol}
                    </span>
                  </div>
                  <span className="mono" style={{ fontSize: '11.5px', fontWeight: 700, color: 'var(--color-green)' }}>
                    +${(w.value_usd || 50000).toLocaleString()}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

      </div>
    </div>
  );
};
