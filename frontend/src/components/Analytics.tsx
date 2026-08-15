import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area,
} from 'recharts';
import { useSimStore } from '../store';

export function AnalyticsDashboard() {
  const metrics = useSimStore((s) => s.metrics);
  const tick = useSimStore((s) => s.tick);
  const agents = useSimStore((s) => s.agents);
  const latest = metrics[metrics.length - 1];

  return (
    <div className="panel analytics">
      <h3>Analytics</h3>
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
        <ResponsiveContainer width="100%" height={100}>
          <AreaChart data={metrics}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1a2332" />
            <XAxis dataKey="tick" tick={{ fill: '#6b7a8f', fontSize: 10 }} />
            <YAxis tick={{ fill: '#6b7a8f', fontSize: 10 }} />
            <Tooltip contentStyle={{ background: '#0d1117', border: '1px solid #30363d' }} />
            <Area type="monotone" dataKey="population" stroke="#00b4d8" fill="#00b4d833" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="chart-block">
        <h4>Energy Balance</h4>
        <ResponsiveContainer width="100%" height={100}>
          <LineChart data={metrics}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1a2332" />
            <XAxis dataKey="tick" tick={{ fill: '#6b7a8f', fontSize: 10 }} />
            <YAxis tick={{ fill: '#6b7a8f', fontSize: 10 }} />
            <Tooltip contentStyle={{ background: '#0d1117', border: '1px solid #30363d' }} />
            <Line type="monotone" dataKey="mean_energy" stroke="#ffd60a" dot={false} />
            <Line type="monotone" dataKey="energy_production" stroke="#00ff88" dot={false} />
            <Line type="monotone" dataKey="energy_consumption" stroke="#e63946" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
