import React from 'react';
import { 
  Terminal, 
  Compass, 
  BookOpen, 
  Users, 
  Brain, 
  Flame, 
  Play, 
  Pause, 
  FlaskConical, 
  Bot,
  Activity
} from 'lucide-react';
import { useTerminalStore } from '../../stores/terminalStore';
import type { TerminalViewType } from '../../stores/terminalStore';
import { setTradingModeApi, togglePauseApi } from '../../services/api';
import type { FeedData } from '../../types/market';

interface HeaderNavProps {
  feed: FeedData | null;
  isConnected: boolean;
  isFallback: boolean;
}

export const HeaderNav: React.FC<HeaderNavProps> = ({ feed, isConnected, isFallback }) => {
  const { 
    activeView, 
    setActiveView, 
    tradingMode, 
    setTradingMode, 
    isPaused, 
    setIsPaused,
    setBacktestModalOpen,
    setAiModalOpen
  } = useTerminalStore();

  const handleToggleMode = async () => {
    const nextMap = { HYBRID: 'SCALP', SCALP: 'SWING', SWING: 'HYBRID' } as const;
    const nextMode = nextMap[tradingMode];
    setTradingMode(nextMode);
    try {
      await setTradingModeApi(nextMode);
    } catch (e) {
      console.error(e);
    }
  };

  const handleTogglePause = async () => {
    const next = !isPaused;
    setIsPaused(next);
    try {
      await togglePauseApi();
    } catch (e) {
      console.error(e);
    }
  };

  const navItems: Array<{ id: TerminalViewType; label: string; icon: any; badge?: string; badgeColor?: string }> = [
    { id: 'terminal', label: 'Terminal', icon: Terminal },
    { id: 'intel', label: 'Intelligence', icon: Compass },
    { id: 'journal', label: 'Journal', icon: BookOpen, badge: 'TODAY', badgeColor: 'var(--color-green)' },
    { id: 'paperclip', label: 'Firm Swarm', icon: Users, badge: '5 AGENTS', badgeColor: 'var(--color-purple)' },
    { id: 'memory', label: 'Memory', icon: Brain },
    { id: 'dexradar', label: 'DEX & Whales', icon: Flame, badge: 'STREAM', badgeColor: 'var(--color-cyan)' },
  ];

  const equityFormatted = feed?.balance_usd 
    ? `$${feed.balance_usd.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` 
    : '$5,250.00';

  const regimeText = feed?.btc_regime?.regime || 'BTC: TRENDING';

  return (
    <header style={{
      height: 'var(--header-height)',
      background: 'var(--bg-surface)',
      borderBottom: '1px solid var(--border-subtle)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 16px',
      gap: '12px',
      flexShrink: 0,
      zIndex: 100,
    }}>
      {/* Left: Brand & Status Cluster */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
        <div style={{
          width: '28px',
          height: '28px',
          background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
          border: '1px solid var(--border-light)',
          borderRadius: 'var(--radius-md)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--color-green)'
        }}>
          <Activity size={16} />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.1 }}>
          <span style={{ fontSize: '13px', fontWeight: 800, letterSpacing: '-0.03em', color: 'var(--text-primary)' }}>
            APEX TERMINAL
          </span>
          <span style={{ fontSize: '9px', fontWeight: 700, color: 'var(--color-blue)', letterSpacing: '0.08em' }}>
            AI DESK
          </span>
        </div>

        <span className="status-pill green" title="Autonomous Trading Desk Engine">
          <span className="pulse-dot" />
          <span>AUTOPILOT LIVE</span>
        </span>

        <span className="status-pill blue" title="Current Market Regime">
          <span className="pulse-dot" style={{ color: 'var(--color-blue)' }} />
          <span>{regimeText}</span>
        </span>

        <span className={`status-pill ${isConnected ? 'green' : 'amber'}`} style={{ fontSize: '9.5px' }}>
          <span className="pulse-dot" />
          <span>{isFallback ? '⚡ SSE POLLING' : (isConnected ? '⚡ SSE LIVE (<50ms)' : 'CONNECTING')}</span>
        </span>
      </div>

      {/* Center: Segmented Navigation Tabs */}
      <nav style={{
        display: 'flex',
        alignItems: 'center',
        background: 'var(--bg-card)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-pill)',
        padding: '3px',
        gap: '2px'
      }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveView(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '4px 10px',
                fontSize: '11.5px',
                fontWeight: 600,
                color: isActive ? 'var(--text-primary)' : 'var(--text-muted)',
                background: isActive ? 'var(--bg-hover)' : 'transparent',
                border: 'none',
                borderRadius: 'var(--radius-pill)',
                cursor: 'pointer',
                transition: 'all 0.12s ease'
              }}
            >
              <Icon size={13} />
              <span>{item.label}</span>
              {item.badge && (
                <span style={{
                  fontSize: '8px',
                  fontWeight: 800,
                  padding: '1px 5px',
                  borderRadius: 'var(--radius-pill)',
                  background: 'rgba(255,255,255,0.06)',
                  color: item.badgeColor || 'var(--text-secondary)'
                }}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Right: Actions & Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
        {/* Equity Badge */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-end',
          padding: '2px 10px',
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-sm)',
          lineHeight: 1.1
        }}>
          <span style={{ fontSize: '8.5px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
            Equity
          </span>
          <span className="mono" style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-green)' }}>
            {equityFormatted}
          </span>
        </div>

        {/* Mode Toggle Button */}
        <button 
          className="btn btn-primary btn-sm" 
          onClick={handleToggleMode}
          title="Toggle Trading Strategy Regime"
        >
          <span>{tradingMode}</span>
        </button>

        {/* Backtest Button */}
        <button 
          className="btn btn-ghost btn-sm" 
          onClick={() => setBacktestModalOpen(true)}
          title="Run Quant Backtest Simulator"
        >
          <FlaskConical size={12} />
          <span>Backtest</span>
        </button>

        {/* Ask AI Button */}
        <button 
          className="btn btn-ghost btn-sm" 
          onClick={() => setAiModalOpen(true)}
          style={{ color: 'var(--color-purple)' }}
          title="Consult Senior AI Quant Officer"
        >
          <Bot size={13} />
          <span>Ask AI</span>
        </button>

        {/* Pause / Resume Button */}
        <button 
          className={`btn btn-sm ${isPaused ? 'btn-danger' : 'btn-ghost'}`} 
          onClick={handleTogglePause}
          title={isPaused ? 'Resume Workstation' : 'Pause Workstation'}
        >
          {isPaused ? <Play size={12} /> : <Pause size={12} />}
          <span>{isPaused ? 'RESUME' : 'PAUSE'}</span>
        </button>
      </div>
    </header>
  );
};
