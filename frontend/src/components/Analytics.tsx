import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { useSimStore } from '../store';

export function AnalyticsDashboard() {
  const metrics = useSimStore((s) => s.metrics);
  const tick = useSimStore((s) => s.tick);
  const agents = useSimStore((s) => s.agents);
  const latest = metrics[metrics.length - 1];

  return (
    <div className="panel analytics">
      <h3>Colony Pulse</h3>
      <div className="stat-grid">
        <div className="stat">
          <span className="stat-value">{agents.length}</span>
          <span className="stat-label">Population</span>
        </div>
        <div className="stat">
          <span className="stat-value">{tick}</span>
          <span className="stat-label">Tick</span>
        </div>
        <div className="stat">
          <span className="stat-value">{latest ? (latest.mean_energy * 100).toFixed(0) : 0}%</span>
          <span className="stat-label">Mean Energy</span>
        </div>
        <div className="stat">
          <span className="stat-value">{latest ? latest.mining_rate.toFixed(1) : 0}</span>
          <span className="stat-label">Mining Rate</span>
        </div>
      </div>

      <div className="chart-block">
        <h4>Population</h4>
        <ResponsiveContainer width="100%" height={80}>
          <AreaChart data={metrics}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1a2332" />
            <XAxis dataKey="tick" hide />
            <YAxis tick={{ fill: '#6b7a8f', fontSize: 9 }} width={28} />
            <Tooltip contentStyle={{ background: '#0d1117', border: '1px solid #30363d' }} />
            <Area type="monotone" dataKey="population" stroke="#38bdf8" fill="#38bdf833" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
