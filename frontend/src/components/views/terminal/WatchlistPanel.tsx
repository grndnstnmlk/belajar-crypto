import React, { useState } from 'react';
import { Search } from 'lucide-react';
import { useTerminalStore } from '../../../stores/terminalStore';
import type { WatchlistItem } from '../../../types/market';

interface WatchlistPanelProps {
  watchlist: WatchlistItem[];
}

export const WatchlistPanel: React.FC<WatchlistPanelProps> = ({ watchlist }) => {
  const { activeSymbol, setActiveSymbol } = useTerminalStore();
  const [search, setSearch] = useState('');

  const filtered = (watchlist || []).filter((c) => {
    const q = search.trim().toLowerCase();
    if (!q) return true;
    return c.symbol.toLowerCase().includes(q) || (c.pair && c.pair.toLowerCase().includes(q));
  });

  return (
    <aside style={{
      width: '260px',
      background: 'var(--bg-surface)',
      borderRight: '1px solid var(--border-subtle)',
      display: 'flex',
      flexDirection: 'column',
      flexShrink: 0,
      overflow: 'hidden'
    }}>
      {/* Header & Search Bar */}
      <div style={{
        padding: '8px 10px',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        gap: '6px'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>
            RS Radar Watchlist
          </span>
          <span className="status-pill blue" style={{ fontSize: '8.5px', padding: '1px 5px' }}>
            {filtered.length} PAIRS
          </span>
        </div>

        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-sm)',
          padding: '4px 8px'
        }}>
          <Search size={12} color="var(--text-muted)" />
          <input
            type="text"
            placeholder="Search coin..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: 'var(--text-primary)',
              fontSize: '11px',
              width: '100%'
            }}
          />
        </div>
      </div>

      {/* List Container */}
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
        {filtered.length === 0 ? (
          <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '11px' }}>
            No pairs found
          </div>
        ) : (
          filtered.map((c) => {
            const isActive = c.symbol === activeSymbol;
            const isUp = (c.change_24h || 0) >= 0;
            const color = isUp ? 'var(--color-green)' : 'var(--color-red)';
            const sign = isUp ? '+' : '';

            return (
              <div
                key={c.symbol}
                onClick={() => setActiveSymbol(c.symbol)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '8px 12px',
                  borderBottom: '1px solid var(--border-subtle)',
                  background: isActive ? 'var(--bg-hover)' : 'transparent',
                  cursor: 'pointer',
                  transition: 'background 0.1s ease'
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontWeight: 700, fontSize: '12px', color: 'var(--text-primary)' }}>
                      {c.symbol}
                    </span>
                    {c.is_leader && (
                      <span style={{
                        fontSize: '8px',
                        fontWeight: 700,
                        padding: '1px 4px',
                        borderRadius: 'var(--radius-sm)',
                        background: 'var(--color-green-dim)',
                        color: 'var(--color-green)'
                      }}>
                        LEADER
                      </span>
                    )}
                  </div>
                  <span style={{ fontSize: '9.5px', color: 'var(--text-muted)' }}>
                    {c.pair || `${c.symbol}USDT`}
                  </span>
                </div>

                <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', gap: '1px' }}>
                  <span className="mono" style={{ fontSize: '11.5px', fontWeight: 600 }}>
                    ${(c.price || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 4 })}
                  </span>
                  <span className="mono" style={{ fontSize: '10px', fontWeight: 600, color }}>
                    {sign}{(c.change_24h || 0).toFixed(2)}%
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
};
