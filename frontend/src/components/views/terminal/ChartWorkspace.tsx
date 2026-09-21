import React, { useEffect, useRef, useState } from 'react';
import { createChart, CandlestickSeries } from 'lightweight-charts';
import type { IChartApi, ISeriesApi } from 'lightweight-charts';
import { RotateCw } from 'lucide-react';
import { useTerminalStore } from '../../../stores/terminalStore';
import type { TimeframeType } from '../../../stores/terminalStore';
import { fetchChartData } from '../../../services/api';

export const ChartWorkspace: React.FC = () => {
  const { activeSymbol, activeTimeframe, setActiveTimeframe } = useTerminalStore();
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartInstanceRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);

  const [currentPrice, setCurrentPrice] = useState<number>(0);
  const [macroInfo, setMacroInfo] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const data = await fetchChartData(activeSymbol, activeTimeframe);
      if (data && data.candles && candleSeriesRef.current) {
        candleSeriesRef.current.setData(data.candles);
        setCurrentPrice(data.current_price || (data.candles[data.candles.length - 1]?.close ?? 0));
        setMacroInfo(data.macro || null);
        chartInstanceRef.current?.timeScale().fitContent();
      }
    } catch (e) {
      console.warn('Failed to load chart data:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Initialize Lightweight Chart
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight,
      layout: {
        background: { color: '#060709' },
        textColor: '#8d96a5',
      },
      grid: {
        vertLines: { color: 'rgba(25, 30, 40, 0.4)' },
        horzLines: { color: 'rgba(25, 30, 40, 0.4)' },
      },
      crosshair: {
        mode: 1,
      },
      timeScale: {
        borderColor: '#191e28',
        timeVisible: true,
      },
    });

    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#00d68f',
      downColor: '#f6465d',
      borderVisible: false,
      wickUpColor: '#00d68f',
      wickDownColor: '#f6465d',
    });

    chartInstanceRef.current = chart;
    candleSeriesRef.current = candlestickSeries;

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    loadData();

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
      chartInstanceRef.current = null;
      candleSeriesRef.current = null;
    };
  }, [activeSymbol, activeTimeframe]);

  const timeframes: TimeframeType[] = ['15m', '1H', '4H'];

  return (
    <div style={{
      flex: 1,
      background: 'var(--bg-canvas)',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      borderRight: '1px solid var(--border-subtle)'
    }}>
      {/* Top Toolbar */}
      <div style={{
        padding: '8px 14px',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'var(--bg-surface)',
        gap: '12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '15px', fontWeight: 800, letterSpacing: '-0.04em', color: 'var(--text-primary)' }}>
            {activeSymbol}/USDT
          </span>
          <span className="mono" style={{ fontSize: '14.5px', fontWeight: 700, color: 'var(--color-green)' }}>
            ${currentPrice.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 4 })}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {/* Timeframe Pills */}
          <div style={{
            display: 'flex',
            background: 'var(--bg-canvas)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-sm)',
            padding: '2px',
            gap: '2px'
          }}>
            {timeframes.map((tf) => (
              <button
                key={tf}
                onClick={() => setActiveTimeframe(tf)}
                style={{
                  background: activeTimeframe === tf ? 'var(--bg-hover)' : 'transparent',
                  color: activeTimeframe === tf ? 'var(--text-primary)' : 'var(--text-muted)',
                  border: 'none',
                  padding: '3px 8px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '10.5px',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                {tf}
              </button>
            ))}
          </div>

          {/* Refresh Button */}
          <button 
            className="btn btn-ghost btn-sm" 
            onClick={loadData}
            title="Force Refresh Klines"
          >
            <RotateCw size={11} className={isLoading ? 'spin-anim' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Chart Canvas Area */}
      <div ref={chartContainerRef} style={{ flex: 1, width: '100%', minHeight: '300px' }} />

      {/* Bottom Metrics Footer */}
      <div style={{
        height: '42px',
        borderTop: '1px solid var(--border-subtle)',
        background: 'var(--bg-surface)',
        display: 'grid',
        gridTemplateColumns: 'repeat(5, 1fr)',
        alignItems: 'center',
        padding: '0 12px',
        gap: '8px',
        flexShrink: 0
      }}>
        <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.1 }}>
          <span style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>ADX Trend</span>
          <span className="mono" style={{ fontSize: '11px', fontWeight: 700, color: 'var(--color-green)' }}>38.4 (Hyper)</span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.1 }}>
          <span style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Parkinson Vol</span>
          <span className="mono" style={{ fontSize: '11px', fontWeight: 700 }}>2.14% (Normal)</span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.1 }}>
          <span style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Macro Shield</span>
          <span className="mono" style={{ fontSize: '11px', fontWeight: 700, color: 'var(--color-green)' }}>🛡️ Green</span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.1 }}>
          <span style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>L2 Depth Imbalance</span>
          <span className="mono" style={{ fontSize: '11px', fontWeight: 700, color: 'var(--color-cyan)' }}>+3.2x Bids Wall</span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.1 }}>
          <span style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>SMC Regime</span>
          <span className="mono" style={{ fontSize: '11px', fontWeight: 700, color: 'var(--color-purple)' }}>
            {macroInfo?.regime || 'Bullish Orderblock'}
          </span>
        </div>
      </div>
    </div>
  );
};
