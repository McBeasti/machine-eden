import { useEffect } from 'react';
import { useSimStore } from './store';
import { WorldCanvas } from './components/WorldCanvas';
import { Controls } from './components/Controls';
import { AgentPanel, EventLog } from './components/AgentPanel';
import { AnalyticsDashboard } from './components/Analytics';
import './App.css';

function WorldLegend() {
  return (
    <div className="world-legend">
      <div className="legend-group">
        <span className="legend-title">Terrain</span>
        <span><i style={{ background: '#1a7a52' }} /> Mineral</span>
        <span><i style={{ background: '#ffc107' }} /> Energy</span>
        <span><i style={{ background: '#22d3ee' }} /> Charge</span>
        <span><i style={{ background: '#ef4444' }} /> Hazard</span>
        <span><i style={{ background: '#a855f7' }} /> Rare</span>
      </div>
      <div className="legend-group">
        <span className="legend-title">Behaviour</span>
        <span><i style={{ background: '#38bdf8' }} /> Move</span>
        <span><i style={{ background: '#fbbf24' }} /> Mine</span>
        <span><i style={{ background: '#f59e0b' }} /> Harvest</span>
        <span><i style={{ background: '#22d3ee' }} /> Charge</span>
        <span><i style={{ background: '#64748b' }} /> Idle</span>
      </div>
    </div>
  );
}

function App() {
  const connect = useSimStore((s) => s.connect);
  const disconnect = useSimStore((s) => s.disconnect);
  const sidebarOpen = useSimStore((s) => s.sidebarOpen);
  const selectedAgentId = useSimStore((s) => s.selectedAgentId);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return (
    <div className={`app ${sidebarOpen ? 'sidebar-open' : ''}`}>
      <Controls />
      <main className="main-layout">
        <section className="world-stage">
          <WorldCanvas />
          <WorldLegend />
          <p className="world-hint">
            Scroll to zoom · drag to pan · click a machine to inspect
            {selectedAgentId ? ' · Focus dims the colony around your selection' : ''}
          </p>
        </section>

        <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`} aria-hidden={!sidebarOpen}>
          <AgentPanel />
          <AnalyticsDashboard />
          <EventLog />
        </aside>
      </main>
    </div>
  );
}

export default App;
