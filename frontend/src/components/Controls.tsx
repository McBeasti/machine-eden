import { useSimStore } from '../store';

const SPEEDS = [0.25, 0.5, 1, 2, 4, 8];

export function Controls() {
  const connected = useSimStore((s) => s.connected);
  const running = useSimStore((s) => s.running);
  const speed = useSimStore((s) => s.speed);
  const config = useSimStore((s) => s.config);
  const sendAction = useSimStore((s) => s.sendAction);
  const reset = useSimStore((s) => s.reset);

  return (
    <div className="controls">
      <div className="brand">
        <h1>MACHINE EDEN</h1>
        <span className="phase">Phase 1 — Visual Foundation</span>
      </div>

      <div className="control-group">
        <span className={`status ${connected ? 'online' : 'offline'}`}>
          {connected ? '● Connected' : '○ Disconnected'}
        </span>
      </div>

      <div className="control-group">
        {!running ? (
          <button className="btn primary" onClick={() => sendAction('start')}>▶ Resume</button>
        ) : (
          <button className="btn" onClick={() => sendAction('pause')}>⏸ Pause</button>
        )}
        <button className="btn" onClick={() => sendAction('step')}>⏭ Step</button>
        <button className="btn danger" onClick={() => reset()}>↺ Reset</button>
      </div>

      <div className="control-group speed">
        <label>Speed</label>
        {SPEEDS.map((s) => (
          <button
            key={s}
            className={`btn sm ${speed === s ? 'active' : ''}`}
            onClick={() => sendAction('speed', { multiplier: s })}
          >
            {s}×
          </button>
        ))}
      </div>

      {config && (
        <div className="config-info">
          <span>Seed: {config.seed}</span>
          <span>World: {config.world_width}×{config.world_height}</span>
          <span>Agents: {config.initial_population}</span>
        </div>
      )}
    </div>
  );
}
