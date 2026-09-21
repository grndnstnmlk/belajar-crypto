import React, { useEffect, useState } from 'react';
import { Users, Bot, RefreshCw } from 'lucide-react';

interface KanbanColumn {
  id: string;
  name: string;
  color: string;
  tickets: any[];
}

export const FirmSwarmView: React.FC = () => {
  const [tickets, setTickets] = useState<any[]>([]);
  const [thoughts, setThoughts] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [ticketsRes, streamRes] = await Promise.all([
        fetch('/api/paperclip/tickets').then((r) => r.json()).catch(() => []),
        fetch('/api/ai/cognitive_stream').then((r) => r.json()).catch(() => []),
      ]);
      setTickets(Array.isArray(ticketsRes) ? ticketsRes : ticketsRes.tickets || []);
      setThoughts(Array.isArray(streamRes) ? streamRes : streamRes.thoughts || []);
    } catch (e) {
      console.warn('Failed to load swarm data:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  const columns: KanbanColumn[] = [
    { id: 'discovered', name: '1. DISCOVERED', color: 'var(--color-blue)', tickets: [] },
    { id: 'debate', name: '2. DEBATE', color: 'var(--color-purple)', tickets: [] },
    { id: 'risk', name: '3. RISK AUDIT', color: 'var(--color-amber)', tickets: [] },
    { id: 'board', name: '4. BOARD APPROVAL', color: 'var(--color-cyan)', tickets: [] },
    { id: 'exec', name: '5. EXECUTION DESK', color: 'var(--color-green)', tickets: [] },
  ];

  // Distribute tickets into columns
  tickets.forEach((t) => {
    const stage = (t.stage || 'discovered').toLowerCase();
    const col = columns.find((c) => c.id === stage) || columns[0];
    col.tickets.push(t);
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
            background: 'rgba(168, 85, 247, 0.12)',
            border: '1px solid rgba(168, 85, 247, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-purple)'
          }}>
            <Users size={20} />
          </div>
          <div>
            <h2 style={{ fontSize: '15px', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
              Paperclip Multi-Agent Swarm Orchestration
            </h2>
            <p style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Decentralized Agent Command: Task Delegation Kanban, Adversarial Debate, and Board Governance.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span className="status-pill green">
            <span className="pulse-dot" />
            <span>SWARM ACTIVE</span>
          </span>
          <button className="btn btn-ghost btn-sm" onClick={loadData} disabled={isLoading}>
            <RefreshCw size={11} className={isLoading ? 'spin-anim' : ''} />
            <span>Heartbeat</span>
          </button>
        </div>
      </div>

      {/* 5-Column Kanban Board */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(5, 1fr)',
        gap: '12px',
        minHeight: '380px'
      }}>
        {columns.map((col) => (
          <div
            key={col.id}
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden'
            }}
          >
            <div style={{
              padding: '10px 12px',
              background: 'var(--bg-card)',
              borderBottom: '1px solid var(--border-subtle)',
              borderTop: `3px solid ${col.color}`,
              fontSize: '11px',
              fontWeight: 700,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <span>{col.name}</span>
              <span className="status-pill blue mono" style={{ fontSize: '9px', padding: '1px 5px' }}>
                {col.tickets.length}
              </span>
            </div>

            <div style={{ padding: '10px', display: 'flex', flexDirection: 'column', gap: '8px', flex: 1, overflowY: 'auto' }}>
              {col.tickets.length === 0 ? (
                <div style={{ padding: '24px 8px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '10.5px' }}>
                  No active tasks
                </div>
              ) : (
                col.tickets.map((t, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: 'var(--bg-card)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '10px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px'
                    }}
                  >
                    <span style={{ fontSize: '11.5px', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {t.title || t.symbol || 'Agent Proposal'}
                    </span>
                    <span style={{ fontSize: '9.5px', color: 'var(--text-muted)' }}>
                      Agent: {t.agent || 'QuantRiskOfficer'}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Local Cognitive Consciousness Stream */}
      <div className="bento-card">
        <div className="bento-card-header">
          <span className="bento-card-title">
            <Bot size={14} />
            <span>{`{ Local Cognitive AI Consciousness Stream }`}</span>
          </span>
          <span className="status-pill purple">ASYNC REASONING WORKER</span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '220px', overflowY: 'auto' }}>
          {thoughts.length === 0 ? (
            <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '11.5px' }}>
              No thoughts streamed yet. AI brain is monitoring active setups.
            </div>
          ) : (
            thoughts.map((item, idx) => (
              <div
                key={idx}
                style={{
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '8px 12px',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '10px'
                }}
              >
                <span className="mono" style={{ fontSize: '10px', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                  {item.timestamp || 'Just now'}
                </span>
                <span style={{ fontSize: '11px', color: 'var(--text-primary)', lineHeight: 1.4 }}>
                  {item.thought || JSON.stringify(item)}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
