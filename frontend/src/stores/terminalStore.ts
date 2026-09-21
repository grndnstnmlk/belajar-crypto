import { create } from 'zustand';

export type TerminalViewType = 'terminal' | 'intel' | 'journal' | 'paperclip' | 'memory' | 'dexradar';
export type TimeframeType = '15m' | '1H' | '4H';
export type OrderSideType = 'BUY' | 'SELL';
export type TradingModeType = 'HYBRID' | 'SCALP' | 'SWING';

interface TerminalState {
  activeView: TerminalViewType;
  activeSymbol: string;
  activeTimeframe: TimeframeType;
  orderSide: OrderSideType;
  riskPct: number;
  tradingMode: TradingModeType;
  isPaused: boolean;
  backtestModalOpen: boolean;
  aiModalOpen: boolean;

  setActiveView: (view: TerminalViewType) => void;
  setActiveSymbol: (sym: string) => void;
  setActiveTimeframe: (tf: TimeframeType) => void;
  setOrderSide: (side: OrderSideType) => void;
  setRiskPct: (risk: number) => void;
  setTradingMode: (mode: TradingModeType) => void;
  setIsPaused: (paused: boolean) => void;
  setBacktestModalOpen: (open: boolean) => void;
  setAiModalOpen: (open: boolean) => void;
}

export const useTerminalStore = create<TerminalState>((set) => ({
  activeView: 'terminal',
  activeSymbol: 'BTC',
  activeTimeframe: '1H',
  orderSide: 'BUY',
  riskPct: 1.5,
  tradingMode: 'HYBRID',
  isPaused: false,
  backtestModalOpen: false,
  aiModalOpen: false,

  setActiveView: (view) => set({ activeView: view }),
  setActiveSymbol: (sym) => set({ activeSymbol: sym }),
  setActiveTimeframe: (tf) => set({ activeTimeframe: tf }),
  setOrderSide: (side) => set({ orderSide: side }),
  setRiskPct: (risk) => set({ riskPct: risk }),
  setTradingMode: (mode) => set({ tradingMode: mode }),
  setIsPaused: (paused) => set({ isPaused: paused }),
  setBacktestModalOpen: (open) => set({ backtestModalOpen: open }),
  setAiModalOpen: (open) => set({ aiModalOpen: open }),
}));
