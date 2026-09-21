import React from 'react';
import { WatchlistPanel } from './terminal/WatchlistPanel';
import { ChartWorkspace } from './terminal/ChartWorkspace';
import { ExecutionPanel } from './terminal/ExecutionPanel';
import type { FeedData } from '../../types/market';

interface TerminalViewProps {
  feed: FeedData | null;
}

export const TerminalView: React.FC<TerminalViewProps> = ({ feed }) => {
  return (
    <main style={{
      flex: 1,
      display: 'flex',
      overflow: 'hidden',
      position: 'relative'
    }}>
      <WatchlistPanel watchlist={feed?.watchlist || []} />
      <ChartWorkspace />
      <ExecutionPanel positions={feed?.positions || []} />
    </main>
  );
};
