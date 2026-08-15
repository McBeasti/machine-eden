import { useSimStore } from '../store';
import { TERRAIN_NAMES } from '../types';

export function AgentPanel() {
  const agent = useSimStore((s) => s.selectedAgent);
  const setSelectedAgent = useSimStore((s) => s.setSelectedAgent);

  if (!agent) {
    return (
      <div className="panel agent-panel empty">
        <h3>Agent Inspector</h3>
        <p className="hint">Click a machine in the world to inspect it.</p>
      </div>
    );
  }

  const lastDecision = agent.decisions?.[agent.decisions.length - 1];

  return (
    <div className="panel agent-panel">
      <div className="panel-header">
        <h3>Agent Inspector</h3>
        <button className="btn-icon" onClick={() => setSelectedAgent(null)}>×</button>
      </div>

      <section>
        <h4>Identity</h4>
        <dl>
          <dt>ID</dt><dd className="mono">{agent.id.slice(0, 8)}…</dd>
          <dt>Generation</dt><dd>{agent.generation}</dd>
          <dt>Age</dt><dd>{agent.age} ticks</dd>
          <dt>Lineage</dt><dd className="mono">{agent.lineage_id.slice(0, 8)}…</dd>
          <dt>Task</dt><dd className="task">{agent.current_task}</dd>
        </dl>
      </section>

      <section>
        <h4>Status</h4>
        <div className="energy-bar">
          <div className="energy-fill" style={{ width: `${agent.energy_ratio * 100}%` }} />
          <span>{agent.energy.toFixed(1)} / {agent.hardware.energy_capacity.toFixed(0)}</span>
        </div>
        <dl>
          <dt>Damage</dt><dd>{agent.damage.toFixed(2)}</dd>
          <dt>Inventory</dt><dd>
            {Object.entries(agent.inventory).length
              ? Object.entries(agent.inventory).map(([k, v]) => `${k}: ${v.toFixed(1)}`).join(', ')
              : 'empty'}
          </dd>
        </dl>
      </section>

      <section>
        <h4>Hardware</h4>
        <dl className="compact">
          <dt>Speed</dt><dd>{agent.hardware.movement_speed.toFixed(2)}</dd>
          <dt>Mining</dt><dd>{agent.hardware.mining_ability.toFixed(2)}</dd>
          <dt>Sensor</dt><dd>{agent.hardware.sensor_range.toFixed(1)}</dd>
          <dt>Capacity</dt><dd>{agent.hardware.carrying_capacity.toFixed(0)}</dd>
        </dl>
      </section>

      {lastDecision && (
        <section>
          <h4>Last Decision</h4>
          <p className="goal">Goal: {lastDecision.current_goal}</p>
          <p className="action">Action: <strong>{lastDecision.selected_action}</strong></p>
          <p className="interpretation">{lastDecision.interpretation}</p>
          <p className="source">Source: {lastDecision.source}</p>
        </section>
      )}
    </div>
  );
}

export function EventLog() {
  const events = useSimStore((s) => s.events);

  return (
    <div className="panel event-log">
      <h3>Event Log</h3>
      <ul>
        {events.slice(0, 30).map((e, i) => (
          <li key={i} className={`event-${e.event_type}`}>
            <span className="tick">T{e.tick}</span>
            <span className="type">{e.event_type}</span>
            {e.actor_id && <span className="actor">{e.actor_id.slice(0, 6)}</span>}
          </li>
        ))}
      </ul>
    </div>
  );
}
