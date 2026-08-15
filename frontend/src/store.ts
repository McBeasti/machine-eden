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
    if (existing?.readyState === WebSocket.OPEN) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const ws = new WebSocket(`${protocol}//${host}/ws/simulation`);

    ws.onopen = () => set({ connected: true, ws });
    ws.onclose = () => set({ connected: false, ws: null, running: false });
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.type === 'state') get().applyState(msg.data);
      if (msg.type === 'tick') get().applyTick(msg.data);
    };
  },

  disconnect: () => {
    get().ws?.close();
    set({ ws: null, connected: false });
  },

  sendAction: (action, payload = {}) => {
    const ws = get().ws;
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action, ...payload }));
      if (action === 'start') set({ running: true });
      if (action === 'pause') set({ running: false });
      if (action === 'speed') set({ speed: payload.multiplier as number });
    }
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
      set({ running: false, tick: 0 });
    }
  },
}));
