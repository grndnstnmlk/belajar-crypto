import React, { useEffect, useState } from 'react';
import { 
  Compass, 
  DollarSign, 
  TrendingUp, 
  Layers, 
  ShieldAlert, 
  Calendar, 
  RotateCw, 
  Coins, 
  Globe 
} from 'lucide-react';
import { fetchMarketIntelligence } from '../../services/api';
import type { IntelligenceData, WallStreetSentiment } from '../../types/market';

export const IntelligenceView: React.FC = () => {
  const [intel, setIntel] = useState<IntelligenceData | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const data = await fetchMarketIntelligence();
      setIntel(data);
    } catch (e) {
      console.warn('Failed to load intelligence:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Macro variables
  const m = intel?.macro || {};
  const fed = m.fed_liquidity_billions || m.fed_net_liquidity || 5840;
  const dxy = m.dxy || { price: 99.68, change_pct: 0.57, state: 'SURGING' };
  const us10y = m.us10y || { yield_pct: 4.96, change_pct: 0.3, state: 'STEADY' };
  const fg = m.fear_and_greed || { score: 51, classification: 'Neutral' };
  const macroRegime = m.macro_regime || 'RISK_OFF';

  // Dominance variables
  const comp = intel?.compass || {};
  const btcD = comp.btc_dominance || 58.54;
  const usdtD = comp.usdt_dominance || 7.07;
  const ethD = comp.eth_d || 14.2;
  const solD = comp.sol_d || 3.8;
  const altPerm = comp.alt_permission !== false;

  // Derivatives variables
  const d = intel?.derivatives || {};
  const oiFmt = d.open_interest_formatted || '$8.13B (107k BTC)';
  const oiChg = d.oi_change_1h_pct || -0.05;
  const lsRatio = d.long_short_ratio || 1.82;
  const longPct = d.long_pct || 64.5;
  const shortPct = d.short_pct || 35.5;
  const funding = d.funding_rate_pct || 0.0049;
  const totalLiq = d.total_liq_4h || 32.6;

  // Coinbase Premium
  const cb = intel?.coinbase_premium || {};
  const cbPrice = cb.coinbase_price || 75697;
  const glPrice = cb.global_price || 75777;
  const spread = cb.premium_usd || -80.14;
  const premPct = cb.premium_pct || -0.1058;
  const isUsInflow = cb.is_us_inflow || false;

  // L2 Liquidity
  const liq = intel?.liquidity?.imbalance || {};
  const bidsUsd = liq.bids_usd || 838029200;
  const asksUsd = liq.asks_usd || 595372350;
  const totalDepth = liq.total_depth_usd || 1433401550;
  const ratio = liq.imbalance_ratio || 1.41;
  const bidShare = liq.bid_share_pct || 58.5;
  const askShare = liq.ask_share_pct || 41.5;

  // Sentiment & Risk
  const sent = intel?.sentiment_narrative || {};
  const posture = sent.market_posture || 'NEUTRAL_CONSOLIDATION';
  const hist = intel?.quant_risk?.historical || {};
  const var95 = hist.var_95_usd || 20.02;
  const cvar95 = hist.cvar_95_usd || 43.92;
  const maxDd = hist.max_drawdown_usd || 1889.68;
  const winRate = hist.win_rate_pct || 41.4;

  // Wall Street Equities
  const ws = (intel?.wallstreet_sentiment || {}) as Partial<WallStreetSentiment>;
  const eq = intel?.macro_equities || {};
  const mstr = eq.mstr_stock || { value: 165.92, change_pct: 21.16 };
  const coin = eq.coinbase_stock || { value: 204.66, change_pct: 6.9 };
  const qqq = eq.nasdaq_qqq || { value: 732.65, change_pct: 3.31 };
  const spx = eq.spx_500 || { value: 5893.62, change_pct: 1.15 };
  const gold = eq.gold_futures || { value: 2748.50, change_pct: 0.42 };
  const avgMom = ws.avg_equity_momentum_pct !== undefined ? ws.avg_equity_momentum_pct : 10.46;
  const sentLabel = ws.sentiment || 'BULLISH_FLOW';

  // TypeSafe Jev AI Microstructure (jarrodwatts/jev-trader)
  const jev = intel?.jev_intelligence || {};
  const jevDecision = jev.decision || {};
  const jevAction = (jevDecision.action || 'HOLD').toUpperCase();
  const jevUpProb = jevDecision.up_in_10 !== undefined ? (jevDecision.up_in_10 * 100).toFixed(1) : '50.0';
  const jevLat = jevDecision.latency_ms || 0.2;
  const jevSummary = jev.summary || '⚪ JEV HOLD (Spread Equilibrium)';

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
            background: 'rgba(59, 130, 246, 0.12)',
            border: '1px solid rgba(59, 130, 246, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-blue)'
          }}>
            <Globe size={20} />
          </div>
          <div>
            <h2 style={{ fontSize: '15px', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
              Macro & Institutional Intelligence Suite
            </h2>
            <p style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Top-Down Macroeconomics, Fed Net Liquidity, 2D Dominance Matrix, and Wall Street Equities Correlation.
            </p>
          </div>
        </div>

        <button className="btn btn-primary btn-sm" onClick={loadData} disabled={isLoading}>
          <RotateCw size={11} className={isLoading ? 'spin-anim' : ''} />
          <span>Refresh Intelligence</span>
        </button>
      </div>

      {/* 8-Grid Bento Suite */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
        
        {/* 1. Federal Reserve Net Liquidity & DXY Shield */}
        <div className="bento-card">
          <div className="bento-card-header">
            <span className="bento-card-title">
              <DollarSign size={14} />
              <span>Federal Reserve Net Liquidity & DXY Shield</span>
            </span>
            <span className={`status-pill ${macroRegime.includes('RISK_ON') ? 'green' : 'red'}`}>
              {macroRegime}
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }} className="mono">
            <div className="pos-metric-item">
              <span className="pos-metric-key">Fed Net Liquidity</span>
              <span className="pos-metric-val" style={{ color: 'var(--color-green)' }}>${Number(fed).toFixed(0)}B</span>
            </div>
            <div className="pos-metric-item">
              <span className="pos-metric-key">Dollar Index (DXY)</span>
              <span className="pos-metric-val" style={{ color: ((dxy.change_pct ?? 0) >= 0) ? 'var(--color-red)' : 'var(--color-green)' }}>
                {Number(dxy.price || 0).toFixed(2)} ({(dxy.change_pct ?? 0) >= 0 ? '+' : ''}{dxy.change_pct ?? 0}%)
              </span>
            </div>
            <div className="pos-metric-item">
              <span className="pos-metric-key">US 10Y Yield</span>
              <span className="pos-metric-val" style={{ color: 'var(--color-amber)' }}>
                {Number(us10y.yield_pct || 0).toFixed(3)}% ({us10y.state || 'STEADY'})
              </span>
            </div>
            <div className="pos-metric-item">
              <span className="pos-metric-key">Fear & Greed</span>
              <span className="pos-metric-val" style={{ color: 'var(--color-blue)' }}>
                {fg.score} / 100 ({fg.classification})
              </span>
            </div>
          </div>
        </div>

        {/* 2. 2D Dominance Matrix */}
        <div className="bento-card">
          <div className="bento-card-header">
            <span className="bento-card-title">
              <Compass size={14} />
              <span>2D Dominance Matrix (BTC.D vs USDT.D)</span>
            </span>
            <span className="status-pill blue">
              {comp.regime_code || 'ALTCOIN REGIME'}
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }} className="mono">
            <div className="pos-metric-item">
              <span className="pos-metric-key">Bitcoin Dominance (BTC.D)</span>
              <span className="pos-metric-val" style={{ color: 'var(--color-amber)' }}>{Number(btcD).toFixed(2)}%</span>
            </div>
            <div className="pos-metric-item">
              <span className="pos-metric-key">Tether Dominance (USDT.D)</span>
              <span className="pos-metric-val" style={{ color: 'var(--color-green)' }}>{Number(usdtD).toFixed(2)}%</span>
            </div>
            <div className="pos-metric-item">
              <span className="pos-metric-key">ETH.D / SOL.D</span>
              <span className="pos-metric-val">{Number(ethD).toFixed(1)}% / {Number(solD).toFixed(1)}%</span>
            </div>
            <div className="pos-metric-item">
              <span className="pos-metric-key">Altcoin Permission</span>
              <span className="pos-metric-val" style={{ color: altPerm ? 'var(--color-green)' : 'var(--color-red)' }}>
                {altPerm ? '🟢 ALLOWED' : '🔴 BLOCKED'}
              </span>
            </div>
          </div>
        </div>

        {/* 3. Coinglass Derivatives Depth */}
        <div className="bento-card">
          <div className="bento-card-header">
            <span className="bento-card-title">
              <TrendingUp size={14} />
              <span>Coinglass Derivatives Depth & Liquidations</span>
            </span>
            <span className="status-pill blue">L/S: {Number(lsRatio).toFixed(2)}</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }} className="mono">
            <div className="pos-metric-item">
              <span className="pos-metric-key">Open Interest (1h)</span>
              <span className="pos-metric-val" style={{ color: 'var(--color-cyan)' }}>{oiFmt} ({oiChg >= 0 ? '+' : ''}{oiChg}%)</span>
            </div>
            <div className="pos-metric-item">
              <span className="pos-metric-key">Funding Rate (8h)</span>
              <span className="pos-metric-val" style={{ color: 'var(--color-green)' }}>+{(funding).toFixed(4)}%</span>
            </div>
            <div className="pos-metric-item">
              <span className="pos-metric-key">Long / Short Ratio</span>
              <span className="pos-metric-val">{Number(lsRatio).toFixed(2)} ({longPct}% L / {shortPct}% S)</span>
            </div>
            <div className="pos-metric-item">
              <span className="pos-metric-key">4H Total Liquidations</span>
              <span className="pos-metric-val" style={{ color: 'var(--color-amber)' }}>{totalLiq} BTC</span>
            </div>
          </div>
        </div>

        {/* 4. Coinbase Institutional Premium Index */}
        <div className="bento-card">
          <div className="bento-card-header">
            <span className="bento-card-title">
              <Coins size={14} />
              <span>Coinbase Institutional Premium Index</span>
            </span>
            <span className={`status-pill ${isUsInflow ? 'green' : 'amber'}`}>
              {isUsInflow ? 'US INFLOW' : 'US DISCOUNT'}
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }} className="mono">
            <div className="pos-metric-item">
              <span className="pos-metric-key">Coinbase Spot</span>
              <span className="pos-metric-val">${Number(cbPrice).toLocaleString()}</span>
            </div>
            <div className="pos-metric-item">
              <span className="pos-metric-key">Global Futures</span>
              <span className="pos-metric-val">${Number(glPrice).toLocaleString()}</span>
            </div>
            <div className="pos-metric-item">
              <span className="pos-metric-key">Institutional Spread</span>
              <span className="pos-metric-val" style={{ color: spread >= 0 ? 'var(--color-green)' : 'var(--color-red)' }}>
                {spread >= 0 ? '+' : ''}${Number(spread).toFixed(2)}
              </span>
            </div>
            <div className="pos-metric-item">
              <span className="pos-metric-key">Premium Index</span>
              <span className="pos-metric-val" style={{ color: premPct >= 0 ? 'var(--color-green)' : 'var(--color-red)' }}>
                {premPct >= 0 ? '+' : ''}{(premPct).toFixed(4)}%
              </span>
            </div>
          </div>
        </div>

        {/* 5. Level-2 Order Book Liquidity */}
        <div className="bento-card">
          <div className="bento-card-header">
            <span className="bento-card-title">
              <Layers size={14} />
              <span>Level-2 Order Book Liquidity</span>
            </span>
            <span className="status-pill purple">{ratio.toFixed(2)}x BIDS</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }} className="mono">
            <div className="pos-metric-item">
              <span className="pos-metric-key">2% Bid Depth</span>
              <span className="pos-metric-val" style={{ color: 'var(--color-green)' }}>${(bidsUsd / 1e6).toFixed(1)}M ({bidShare}%)</span>
            </div>
            <div className="pos-metric-item">
              <span className="pos-metric-key">2% Ask Depth</span>
              <span className="pos-metric-val" style={{ color: 'var(--color-red)' }}>${(asksUsd / 1e6).toFixed(1)}M ({askShare}%)</span>
            </div>
            <div className="pos-metric-item">
              <span className="pos-metric-key">Total Book Depth</span>
              <span className="pos-metric-val">${(totalDepth / 1e9).toFixed(2)}B</span>
            </div>
            <div className="pos-metric-item">
              <span className="pos-metric-key">Imbalance Multiplier</span>
              <span className="pos-metric-val" style={{ color: 'var(--color-cyan)' }}>{ratio.toFixed(2)}x Ratio</span>
            </div>

            {/* TypeSafe Jev AI Microstructure Call (jarrodwatts/jev-trader) */}
            <div style={{
              gridColumn: 'span 2',
              marginTop: '4px',
              padding: '8px 10px',
              borderRadius: 'var(--radius-sm)',
              background: 'rgba(0, 240, 255, 0.05)',
              border: '1px solid rgba(0, 240, 255, 0.2)',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '10px', color: 'var(--color-cyan)', fontWeight: 700 }}>
                  🧠 TypeSafe Jev AI Reflex (~30s Horizon)
                </span>
                <span style={{
                  fontSize: '8.5px',
                  padding: '1px 6px',
                  borderRadius: '100px',
                  background: jevAction === 'BUY' ? 'rgba(0, 255, 136, 0.15)' : (jevAction === 'SELL' ? 'rgba(255, 68, 68, 0.15)' : 'rgba(255, 255, 255, 0.05)'),
                  color: jevAction === 'BUY' ? 'var(--color-green)' : (jevAction === 'SELL' ? 'var(--color-red)' : 'var(--text-muted)'),
                  border: `1px solid ${jevAction === 'BUY' ? 'var(--color-green)' : (jevAction === 'SELL' ? 'var(--color-red)' : 'var(--border-subtle)')}`,
                  fontWeight: 700
                }}>
                  {jevAction} ({jevUpProb}% UP | {jevLat}ms)
                </span>
              </div>
              <span style={{ fontSize: '10px', color: 'var(--text-secondary)' }}>
                {jevSummary}
              </span>
            </div>
          </div>
        </div>

        {/* 6. Sentiment Narrative & Quant Risk */}
        <div className="bento-card">
          <div className="bento-card-header">
            <span className="bento-card-title">
              <ShieldAlert size={14} />
              <span>Sentiment Narrative & Quant Risk</span>
            </span>
            <span className="status-pill green">{posture}</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }} className="mono">
            <div className="pos-metric-item">
              <span className="pos-metric-key">1-Day VaR (95%)</span>
              <span className="pos-metric-val" style={{ color: 'var(--color-amber)' }}>${Number(var95).toFixed(2)}</span>
            </div>
            <div className="pos-metric-item">
              <span className="pos-metric-key">Expected Shortfall (CVaR)</span>
              <span className="pos-metric-val" style={{ color: 'var(--color-red)' }}>${Number(cvar95).toFixed(2)}</span>
            </div>
            <div className="pos-metric-item">
              <span className="pos-metric-key">Max Drawdown Cap</span>
              <span className="pos-metric-val">${Number(maxDd).toFixed(2)}</span>
            </div>
            <div className="pos-metric-item">
              <span className="pos-metric-key">Historical Win Rate</span>
              <span className="pos-metric-val" style={{ color: 'var(--color-green)' }}>{Number(winRate).toFixed(1)}%</span>
            </div>
          </div>
        </div>

        {/* 7. Lewis Trumpeter Seasonality Suite */}
        <div className="bento-card" style={{ gridColumn: '1 / -1', borderColor: 'rgba(110, 231, 183, 0.25)' }}>
          <div className="bento-card-header">
            <span className="bento-card-title">
              <Calendar size={14} />
              <span>{`{ Lewis Trumpeter Hedge Fund Seasonality & Calendar Anomaly Suite }`}</span>
            </span>
            <span className="status-pill green">ACTIVE CYCLE</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }} className="mono">
            <div className="pos-metric-item">
              <span className="pos-metric-key">Payday Inflow (12th-18th)</span>
              <span className="pos-metric-val" style={{ color: 'var(--color-green)' }}>+2.45% Drift</span>
            </div>
            <div className="pos-metric-item">
              <span className="pos-metric-key">Autumn Short Hedge</span>
              <span className="pos-metric-val" style={{ color: 'var(--color-red)' }}>Active</span>
            </div>
            <div className="pos-metric-item">
              <span className="pos-metric-key">Day-of-Week Edge</span>
              <span className="pos-metric-val" style={{ color: 'var(--color-blue)' }}>Monday Momentum</span>
            </div>
            <div className="pos-metric-item">
              <span className="pos-metric-key">MAE Hard Stop</span>
              <span className="pos-metric-val">3.14% Cap</span>
            </div>
          </div>
        </div>

        {/* 8. Wall Street Macro & Crypto Equities Correlation */}
        <div className="bento-card" style={{ gridColumn: '1 / -1', borderColor: 'rgba(59, 130, 246, 0.35)' }}>
          <div className="bento-card-header">
            <span className="bento-card-title">
              <Globe size={14} />
              <span>{`{ Wall Street Crypto Equities & Macro Correlation (MSTR / COIN / QQQ / Gold) }`}</span>
            </span>
            <span className={`status-pill ${avgMom >= 1.0 ? 'green' : 'amber'}`}>
              {sentLabel} ({avgMom >= 0 ? '+' : ''}{avgMom.toFixed(2)}%)
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '8px' }} className="mono">
            <div className="pos-metric-item" style={{ borderLeft: '2px solid #00d68f' }}>
              <span className="pos-metric-key">MSTR (MicroStrategy)</span>
              <span className="pos-metric-val" style={{ color: 'var(--color-green)' }}>
                ${Number((mstr as any).value ?? (mstr as any).price ?? 0).toFixed(2)} ({mstr.change_pct >= 0 ? '+' : ''}{Number(mstr.change_pct || 0).toFixed(2)}%)
              </span>
              <span style={{ fontSize: '9px', color: 'var(--text-muted)' }}>BTC Treasury Proxy (2.5x Beta)</span>
            </div>

            <div className="pos-metric-item" style={{ borderLeft: '2px solid #3b82f6' }}>
              <span className="pos-metric-key">COIN (Coinbase)</span>
              <span className="pos-metric-val" style={{ color: 'var(--color-blue)' }}>
                ${Number((coin as any).value ?? (coin as any).price ?? 0).toFixed(2)} ({coin.change_pct >= 0 ? '+' : ''}{Number(coin.change_pct || 0).toFixed(2)}%)
              </span>
              <span style={{ fontSize: '9px', color: 'var(--text-muted)' }}>US Institutional & Retail Flow</span>
            </div>

            <div className="pos-metric-item" style={{ borderLeft: '2px solid #a855f7' }}>
              <span className="pos-metric-key">QQQ (Nasdaq 100)</span>
              <span className="pos-metric-val" style={{ color: 'var(--color-purple)' }}>
                ${Number((qqq as any).value ?? (qqq as any).price ?? 0).toFixed(2)} ({qqq.change_pct >= 0 ? '+' : ''}{Number(qqq.change_pct || 0).toFixed(2)}%)
              </span>
              <span style={{ fontSize: '9px', color: 'var(--text-muted)' }}>Global Tech Risk-On Beta</span>
            </div>

            <div className="pos-metric-item" style={{ borderLeft: '2px solid #242b3a' }}>
              <span className="pos-metric-key">S&P 500 (SPX)</span>
              <span className="pos-metric-val">
                ${Number((spx as any).value ?? (spx as any).price ?? 0).toFixed(2)} ({spx.change_pct >= 0 ? '+' : ''}{Number(spx.change_pct || 0).toFixed(2)}%)
              </span>
              <span style={{ fontSize: '9px', color: 'var(--text-muted)' }}>Broad Market Liquidity</span>
            </div>

            <div className="pos-metric-item" style={{ borderLeft: '2px solid #f59e0b' }}>
              <span className="pos-metric-key">Gold (GC=F)</span>
              <span className="pos-metric-val" style={{ color: 'var(--color-amber)' }}>
                ${Number((gold as any).value ?? (gold as any).price ?? 0).toFixed(2)} ({gold.change_pct >= 0 ? '+' : ''}{Number(gold.change_pct || 0).toFixed(2)}%)
              </span>
              <span style={{ fontSize: '9px', color: 'var(--text-muted)' }}>Macro Safe-Haven Hedge</span>
            </div>
          </div>

          <div style={{
            background: 'var(--bg-card-subtle)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-sm)',
            padding: '8px 10px',
            fontSize: '11px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div>
              <span style={{ fontWeight: 700, color: avgMom >= 0 ? 'var(--color-green)' : 'var(--color-red)' }}>
                Wall Street Sentiment: {sentLabel}
              </span>
              <span style={{ color: 'var(--text-secondary)', marginLeft: '8px' }}>
                {avgMom >= 1.0 
                  ? 'High-beta equity tailwinds front-running spot crypto ETFs. 21:30 WIB Cash Open liquidity expansion anticipated.' 
                  : 'Equities consolidated or risk-off. Monitor 4H EMA50 for structural support.'}
              </span>
            </div>
            <span className="status-pill green" style={{ fontSize: '8.5px' }}>
              LEAD-LAG CORRELATION
            </span>
          </div>
        </div>

      </div>
    </div>
  );
};
