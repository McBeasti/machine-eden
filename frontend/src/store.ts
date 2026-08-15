import { create } from 'zustand';
import type { Agent, SimConfig, SimEvent, SimulationState, TickMetrics, WorldState } from './types';

const API = '/api';

interface SimStore {
  connected: boolean;
  running: boolean;
  speed: number;
  tick: number;
  config: SimConfig | null;
  world: WorldState | null;
  agents: Agent[];
  metrics: TickMetrics[];
  events: SimEvent[];
  selectedAgentId: string | null;
  selectedAgent: Agent | null;
  ws: WebSocket | null;

  setConnected: (v: boolean) => void;
  setSelectedAgent: (id: string | null) => void;
  applyState: (state: Partial<SimulationState>) => void;
  applyTick: (data: { tick: number; agents: Agent[]; metrics: TickMetrics; events: SimEvent[] }) => void;
  connect: () => void;
  disconnect: () => void;
  sendAction: (action: string, payload?: Record<string, unknown>) => void;
  start: () => Promise<void>;
  pause: () => Promise<void>;
  step: () => Promise<void>;
  setSpeed: (multiplier: number) => Promise<void>;
  fetchAgent: (id: string) => Promise<void>;
  reset: (config?: Partial<SimConfig>) => Promise<void>;
}

export const useSimStore = create<SimStore>((set, get) => ({
  connected: false,
  running: false,
  speed: 1,
  tick: 0,
  config: null,
  world: null,
  agents: [],
  metrics: [],
  events: [],
  selectedAgentId: null,
  selectedAgent: null,
  ws: null,

  setConnected: (v) => set({ connected: v }),
  setSelectedAgent: (id) => set({ selectedAgentId: id, selectedAgent: null }),

  applyState: (state) =>
    set({
      tick: state.tick ?? get().tick,
      running: state.running ?? get().running,
      speed: state.speed ?? get().speed,
      config: state.config ?? get().config,
      world: state.world ?? get().world,
      agents: state.agents ?? get().agents,
      metrics: state.metrics ?? get().metrics,
      events: state.events ?? get().events,
    }),

  applyTick: (data) =>
    set((s) => ({
      tick: data.tick,
      agents: data.agents,
      metrics: [...s.metrics.slice(-199), data.metrics],
      events: [...data.events, ...s.events].slice(0, 200),
    })),

  connect: () => {
    const existing = get().ws;
    if (existing && (existing.readyState === WebSocket.OPEN || existing.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const ws = new WebSocket(`${protocol}//${host}/ws/simulation`);

    ws.onopen = () => {
      if (get().ws && get().ws !== ws && get().ws?.readyState === WebSocket.OPEN) {
        ws.close();
        return;
      }
      set({ connected: true, ws });
    };
    ws.onclose = () => {
      // Ignore close from a superseded StrictMode socket
      if (get().ws !== ws && get().ws != null) return;
      set({ connected: false, ws: null, running: false });
    };
    ws.onerror = () => {
      // onclose will follow; keep store consistent if this was the active socket
      if (get().ws === ws) set({ connected: false });
    };
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.type === 'state') get().applyState(msg.data);
      if (msg.type === 'tick') get().applyTick(msg.data);
    };

    // Assign early so disconnect/StrictMode can target this socket
    set({ ws });
  },

  disconnect: () => {
    const ws = get().ws;
    if (ws) {
      ws.onclose = null;
      ws.close();
    }
    set({ ws: null, connected: false });
  },

  // Prefer REST for controls (reliable); keep WS for live tick streaming.
  sendAction: (action, payload = {}) => {
    if (action === 'start') void get().start();
    else if (action === 'pause') void get().pause();
    else if (action === 'step') void get().step();
    else if (action === 'speed') void get().setSpeed(payload.multiplier as number);
    else {
      const ws = get().ws;
      if (ws?.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action, ...payload }));
      }
    }
  },

  start: async () => {
    const res = await fetch(`${API}/simulation/start`, { method: 'POST' });
    if (res.ok) set({ running: true });
  },

  pause: async () => {
    const res = await fetch(`${API}/simulation/pause`, { method: 'POST' });
    if (res.ok) set({ running: false });
  },

  step: async () => {
    const res = await fetch(`${API}/simulation/step`, { method: 'POST' });
    if (res.ok) {
      const delta = await res.json();
      get().applyTick(delta);
      set({ running: false });
    }
  },

  setSpeed: async (multiplier: number) => {
    const res = await fetch(`${API}/simulation/speed`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ multiplier }),
    });
    if (res.ok) set({ speed: multiplier });
  },

  fetchAgent: async (id) => {
    const res = await fetch(`${API}/agents/${id}`);
    if (res.ok) {
      const agent = await res.json();
      set({ selectedAgent: agent });
    }
  },

  reset: async (config) => {
    const res = await fetch(`${API}/simulation/reset`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config ?? {}),
    });
    if (res.ok) {
      const state = await res.json();
      get().applyState(state);
      set({ running: false, tick: state.tick ?? 0 });
    }
  },
}));
