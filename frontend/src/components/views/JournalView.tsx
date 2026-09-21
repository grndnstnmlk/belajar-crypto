import React, { useEffect, useState } from 'react';
import { BookOpen, RefreshCw } from 'lucide-react';
import { fetchJournal } from '../../services/api';
import type { JournalMetrics, JournalTrade } from '../../types/market';

export const JournalView: React.FC = () => {
  const [metrics, setMetrics] = useState<JournalMetrics>({});
  const [ledger, setLedger] = useState<JournalTrade[]>([]);
  const [filter, setFilter] = useState<'today' | 'all'>('today');
  const [isLoading, setIsLoading] = useState(false);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const data = await fetchJournal();
      setMetrics(data.metrics || {});
      setLedger(data.ledger || []);
    } catch (e) {
      console.warn('Failed to load journal:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const filteredLedger = (ledger || []).filter((t) => {
    if (filter === 'all') return true;
    const todayStr = new Date().toISOString().slice(0, 10);
    return t.close_time && t.close_time.startsWith(todayStr);
  });

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Header Banner */}
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
            background: 'rgba(0, 214, 143, 0.12)',
            border: '1px solid rgba(0, 214, 143, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-green)'
          }}>
            <BookOpen size={20} />
          </div>
          <div>
            <h2 style={{ fontSize: '15px', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
              Institutional Trade Journal & Execution Ledger
            </h2>
            <p style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Real-time Binance Futures closed trade audit, Math Expectancy, and SMC post-mortem autopsy.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            className={`btn btn-sm ${filter === 'today' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setFilter('today')}
          >
            ⭐ Today
          </button>
          <button
            className={`btn btn-sm ${filter === 'all' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setFilter('all')}
          >
            Show All
          </button>
          <button className="btn btn-ghost btn-sm" onClick={loadData} disabled={isLoading}>
            <RefreshCw size={11} className={isLoading ? 'spin-anim' : ''} />
            <span>Sync</span>
          </button>
        </div>
      </div>

      {/* 6-Grid Scorecard */}
      <div className="scorecard-grid">
        <div className="scorecard-item">
          <span className="scorecard-key">Win Rate %</span>
          <span className="scorecard-val mono" style={{ color: 'var(--color-green)' }}>
            {(metrics.win_rate_pct || 0).toFixed(1)}%
          </span>
        </div>
        <div className="scorecard-item">
          <span className="scorecard-key">Profit Factor</span>
          <span className="scorecard-val mono">
            {(metrics.profit_factor || 0).toFixed(2)}
          </span>
        </div>
        <div className="scorecard-item">
          <span className="scorecard-key">Math Expectancy</span>
          <span className="scorecard-val mono" style={{ color: (metrics.math_expectancy || 0) >= 0 ? 'var(--color-green)' : 'var(--color-red)' }}>
            {(metrics.math_expectancy || 0) >= 0 ? '+' : ''}${(metrics.math_expectancy || 0).toFixed(2)}
          </span>
        </div>
        <div className="scorecard-item">
          <span className="scorecard-key">Payoff Ratio</span>
          <span className="scorecard-val mono">
            {(metrics.payoff_ratio || 0).toFixed(2)}
          </span>
        </div>
        <div className="scorecard-item">
          <span className="scorecard-key">Net Realized PnL</span>
          <span className="scorecard-val mono" style={{ color: (metrics.net_pnl_usd || 0) >= 0 ? 'var(--color-green)' : 'var(--color-red)' }}>
            {(metrics.net_pnl_usd || 0) >= 0 ? '+' : ''}${(metrics.net_pnl_usd || 0).toFixed(2)}
          </span>
        </div>
        <div className="scorecard-item">
          <span className="scorecard-key">Total Trades</span>
          <span className="scorecard-val mono">
            {metrics.total_trades || 0}
          </span>
        </div>
      </div>

      {/* Closed Trades Ledger Table */}
      <div className="bento-card">
        <div className="bento-card-header">
          <span className="bento-card-title">
            <span>Closed Trades Ledger</span>
            <span className="status-pill blue">{filteredLedger.length} TRADES</span>
          </span>
        </div>

        <div className="data-table-wrap">
          <table className="data-table mono">
            <thead>
              <tr>
                <th>Close Time</th>
                <th>Symbol</th>
                <th>Side</th>
                <th>Strategy</th>
                <th>Entry</th>
                <th>Exit</th>
                <th>Net PnL</th>
                <th>R:R</th>
                <th>SMC Autopsy / Exit Reason</th>
              </tr>
            </thead>
            <tbody>
              {filteredLedger.length === 0 ? (
                <tr>
                  <td colSpan={9} style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                    No closed trades found for this period.
                  </td>
                </tr>
              ) : (
                filteredLedger.map((t, idx) => {
                  const isLong = (t.side || '').toUpperCase() === 'LONG' || (t.side || '').toUpperCase() === 'BUY';
                  const pnl = t.net_pnl ?? t.realized_pnl ?? 0;
                  const isProfit = pnl >= 0;

                  return (
                    <tr key={idx}>
                      <td style={{ color: 'var(--text-secondary)' }}>{t.close_time}</td>
                      <td style={{ fontWeight: 700 }}>{t.symbol}</td>
                      <td>
                        <span className={`status-pill ${isLong ? 'green' : 'red'}`} style={{ fontSize: '8.5px', padding: '1px 5px' }}>
                          {t.side}
                        </span>
                      </td>
                      <td style={{ color: 'var(--text-secondary)' }}>{t.strategy}</td>
                      <td>${(t.entry_price || 0).toLocaleString()}</td>
                      <td>${(t.exit_price || 0).toLocaleString()}</td>
                      <td style={{ fontWeight: 700, color: isProfit ? 'var(--color-green)' : 'var(--color-red)' }}>
                        {isProfit ? '+' : ''}${pnl.toFixed(2)}
                      </td>
                      <td style={{ color: isProfit ? 'var(--color-green)' : 'var(--color-red)' }}>
                        {t.r_multiple !== undefined ? `${t.r_multiple > 0 ? '+' : ''}${t.r_multiple}R` : '-'}
                      </td>
                      <td style={{ fontSize: '10.5px', color: 'var(--text-muted)' }}>{t.exit_reason || 'Target hit / SL trail'}</td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
