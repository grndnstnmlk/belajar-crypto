import React from 'react';
import './styles/tokens.css';
import { useTerminalStore } from './stores/terminalStore';
import { useSSEFeed } from './hooks/useSSEFeed';
import { HeaderNav } from './components/layout/HeaderNav';
import { TerminalView } from './components/views/TerminalView';
import { IntelligenceView } from './components/views/IntelligenceView';
import { JournalView } from './components/views/JournalView';
import { FirmSwarmView } from './components/views/FirmSwarmView';
import { MemoryView } from './components/views/MemoryView';
import { DexRadarView } from './components/views/DexRadarView';
import { BacktestModal } from './components/modals/BacktestModal';
import { AiOfficerModal } from './components/modals/AiOfficerModal';

export const App: React.FC = () => {
  const { activeView } = useTerminalStore();
  const { feed, isConnected, isFallback } = useSSEFeed();

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      width: '100vw',
      overflow: 'hidden',
      background: 'var(--bg-canvas)'
    }}>
      <HeaderNav feed={feed} isConnected={isConnected} isFallback={isFallback} />

      {activeView === 'terminal' && <TerminalView feed={feed} />}
      {activeView === 'intel' && <IntelligenceView />}
      {activeView === 'journal' && <JournalView />}
      {activeView === 'paperclip' && <FirmSwarmView />}
      {activeView === 'memory' && <MemoryView />}
      {activeView === 'dexradar' && <DexRadarView />}

      <BacktestModal />
      <AiOfficerModal />
    </div>
  );
};

export default App;
