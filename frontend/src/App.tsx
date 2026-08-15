import { useEffect } from 'react';
import { useSimStore } from './store';
import { WorldCanvas } from './components/WorldCanvas';
import { Controls } from './components/Controls';
import { AgentPanel, EventLog } from './components/AgentPanel';
import { AnalyticsDashboard } from './components/Analytics';
import './App.css';

function App() {
  const connect = useSimStore((s) => s.connect);
  const disconnect = useSimStore((s) => s.disconnect);
  const world = useSimStore((s) => s.world);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  const canvasW = 800;
  const canvasH = 600;

  return (
    <div className="app">
      <Controls />
      <main className="main-layout">
        <div className="world-section">
          <WorldCanvas width={canvasW} height={canvasH} />
          <div className="legend">
            <span style={{ color: '#2d6a4f' }}>● Mineral</span>
            <span style={{ color: '#ffd60a' }}>● Energy</span>
            <span style={{ color: '#00b4d8' }}>● Charging</span>
            <span style={{ color: '#e63946' }}>● Hazard</span>
            <span style={{ color: '#7b2cbf' }}>● Rare</span>
          </div>
        </div>
        <aside className="sidebar">
          <AgentPanel />
          <AnalyticsDashboard />
          <EventLog />
        </aside>
      </main>
      <footer className="footer">
        Machine Eden v0.1 — Emergent behaviour from local rules, not scripted stories.
        {world && ` World: ${world.width}×${world.height}`}
      </footer>
    </div>
  );
}

export default App;
