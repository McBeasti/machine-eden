import { useSimStore } from '../store';

const SPEEDS = [0.25, 0.5, 1, 2, 4, 8];

export function Controls() {
  const connected = useSimStore((s) => s.connected);
  const running = useSimStore((s) => s.running);
  const speed = useSimStore((s) => s.speed);
  const config = useSimStore((s) => s.config);
  const tick = useSimStore((s) => s.tick);
  const agents = useSimStore((s) => s.agents);
  const start = useSimStore((s) => s.start);
  const pause = useSimStore((s) => s.pause);
  const step = useSimStore((s) => s.step);
  const setSpeed = useSimStore((s) => s.setSpeed);
  const reset = useSimStore((s) => s.reset);
  const showTrails = useSimStore((s) => s.showTrails);
  const showActivity = useSimStore((s) => s.showActivity);
  const focusMode = useSimStore((s) => s.focusMode);
  const setShowTrails = useSimStore((s) => s.setShowTrails);
  const setShowActivity = useSimStore((s) => s.setShowActivity);
  const setFocusMode = useSimStore((s) => s.setFocusMode);
  const sidebarOpen = useSimStore((s) => s.sidebarOpen);
  const setSidebarOpen = useSimStore((s) => s.setSidebarOpen);

  return (
    <header className="controls">
      <div className="brand">
        <h1>MACHINE EDEN</h1>
        <span className="phase">Living Colony — Visual Foundation</span>
      </div>

      <div className="control-group">
        <span className={`status ${connected ? 'online' : 'offline'}`}>
          {connected ? '● Connected' : '○ Disconnected'}
        </span>
      </div>

      <div className="control-group">
        {!running ? (
          <button className="btn primary" onClick={() => void start()}>▶ Resume</button>
        ) : (
          <button className="btn" onClick={() => void pause()}>⏸ Pause</button>
        )}
        <button className="btn" onClick={() => void step()}>⏭ Step</button>
        <button className="btn danger" onClick={() => void reset()}>↺ Reset</button>
      </div>

      <div className="control-group speed">
        <label>Speed</label>
        {SPEEDS.map((s) => (
          <button
            key={s}
            className={`btn sm ${speed === s ? 'active' : ''}`}
            onClick={() => void setSpeed(s)}
          >
            {s}×
          </button>
        ))}
      </div>

      <div className="control-group overlays">
        <label>View</label>
        <button
          className={`btn sm ${showTrails ? 'active' : ''}`}
          onClick={() => setShowTrails(!showTrails)}
          title="Motion trails and intent beams"
        >
          Trails
        </button>
        <button
          className={`btn sm ${showActivity ? 'active' : ''}`}
          onClick={() => setShowActivity(!showActivity)}
          title="Recent mining / energy activity heat"
        >
          Activity
        </button>
        <button
          className={`btn sm ${focusMode ? 'active' : ''}`}
          onClick={() => setFocusMode(!focusMode)}
          title="Dim other agents when one is selected"
        >
          Focus
        </button>
        <button
          className={`btn sm ${sidebarOpen ? 'active' : ''}`}
          onClick={() => setSidebarOpen(!sidebarOpen)}
        >
          Data
        </button>
      </div>

      <div className="config-info">
        <span>T{tick}</span>
        <span>{agents.length} alive</span>
        {config && (
          <>
            <span>Seed {config.seed}</span>
            <span>{config.world_width}×{config.world_height}</span>
          </>
        )}
      </div>
    </header>
  );
}
