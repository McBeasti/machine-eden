import { useEffect, useRef, useState, useCallback } from 'react';
import { Application, Container, Graphics } from 'pixi.js';
import { useSimStore } from '../store';
import type { Agent, WorldState } from '../types';
import {
  CELL,
  TERRAIN_GLOW,
  TERRAIN_HEX,
  lineageColor,
  taskColor,
} from '../render/palette';
import {
  createCamera,
  easeCamera,
  fitCameraToWorld,
  focusOnCell,
  type CameraState,
} from '../render/camera';
import {
  createAgentVisual,
  syncAgentVisual,
  tickAgentVisual,
  type AgentVisual,
} from '../render/agentVisuals';

interface ActivityMark {
  x: number;
  y: number;
  kind: string;
  age: number;
}

function buildTerrainLayers(world: WorldState, time: number): { base: Graphics; glow: Graphics } {
  const base = new Graphics();
  const glow = new Graphics();
  const w = world.width;
  const h = world.height;

  // Soft ground plane
  base.rect(0, 0, w * CELL, h * CELL);
  base.fill(0x050810);

  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const terrain = world.terrain[y][x];
      const resource = world.resources[y][x];
      const px = x * CELL;
      const py = y * CELL;
      const color = TERRAIN_HEX[terrain] ?? 0x070b12;

      if (terrain === 0) {
        // Subtle noise speckles for empty cells
        if ((x * 17 + y * 31) % 23 === 0) {
          base.rect(px + 2, py + 2, 2, 2);
          base.fill({ color: 0x0e1520, alpha: 0.55 });
        }
        continue;
      }

      base.rect(px, py, CELL, CELL);
      base.fill({ color, alpha: 0.55 + Math.min(0.35, resource / 80) });

      const glowColor = TERRAIN_GLOW[terrain];
      if (!glowColor) continue;

      const cx = px + CELL / 2;
      const cy = py + CELL / 2;
      const pulse =
        terrain === 4 || terrain === 5
          ? 0.55 + 0.25 * Math.sin(time * 2.2 + x * 0.3 + y * 0.2)
          : terrain === 6
            ? 0.4 + 0.3 * Math.sin(time * 3.5 + x + y)
            : 0.35 + Math.min(0.4, resource / 60);

      const radius = CELL * (0.55 + Math.min(0.7, resource / 40));
      glow.circle(cx, cy, radius * 1.6);
      glow.fill({ color: glowColor, alpha: pulse * 0.18 });
      glow.circle(cx, cy, radius * 0.7);
      glow.fill({ color: glowColor, alpha: pulse * 0.45 });
    }
  }

  return { base, glow };
}

function drawAgentBody(
  g: Graphics,
  agent: Agent,
  vx: number,
  vy: number,
  visual: AgentVisual,
  selected: boolean,
  dimmed: boolean,
  showIntent: boolean,
  time: number,
): void {
  const size = 3.2 + agent.hardware.chassis_size * 2.4;
  const body = lineageColor(agent.lineage_id);
  const task = taskColor(agent.current_task);
  const alphaMul = dimmed ? 0.22 : 1;

  // Trail
  for (let i = 0; i < visual.trail.length; i++) {
    const p = visual.trail[i];
    const t = 1 - p.age / 1.6;
    g.circle(p.x * CELL + CELL / 2, p.y * CELL + CELL / 2, size * 0.35 * t);
    g.fill({ color: task, alpha: 0.15 * t * alphaMul });
  }

  // Intent beam
  if (
    showIntent &&
    !dimmed &&
    agent.intent_x != null &&
    agent.intent_y != null &&
    (agent.intent_x !== agent.x || agent.intent_y !== agent.y)
  ) {
    const tx = agent.intent_x * CELL + CELL / 2;
    const ty = agent.intent_y * CELL + CELL / 2;
    g.moveTo(vx, vy);
    g.lineTo(tx, ty);
    g.stroke({ width: 1.2, color: task, alpha: 0.35 * alphaMul });
    g.circle(tx, ty, 2.5);
    g.fill({ color: task, alpha: 0.5 * alphaMul });
  }

  // Energy aura
  const energyR = size + 3 + agent.energy_ratio * 3;
  g.circle(vx, vy, energyR);
  g.stroke({
    width: 1.5,
    color: 0x34d399,
    alpha: (0.25 + agent.energy_ratio * 0.65) * alphaMul,
  });

  // Task ring
  g.circle(vx, vy, size + 1.5);
  g.stroke({ width: 2, color: task, alpha: (0.55 + visual.flash * 0.4) * alphaMul });

  // Body
  g.circle(vx, vy, size);
  g.fill({ color: body, alpha: (agent.current_task === 'idle' ? 0.55 : 0.92) * alphaMul });

  // Heading notch for movement
  if (agent.current_task === 'move' || agent.current_task === 'explore') {
    const angle = Math.atan2(
      (agent.intent_y ?? agent.y) - visual.displayY,
      (agent.intent_x ?? agent.x) - visual.displayX,
    );
    const nx = vx + Math.cos(angle) * (size + 2);
    const ny = vy + Math.sin(angle) * (size + 2);
    g.circle(nx, ny, 1.6);
    g.fill({ color: 0xe0f2fe, alpha: 0.9 * alphaMul });
  }

  // Action flash
  if (visual.flash > 0) {
    g.circle(vx, vy, size + 4 + visual.flash * 6);
    g.stroke({ width: 2, color: task, alpha: visual.flash * 0.7 * alphaMul });
  }

  // Selection pulse
  if (selected) {
    const pulse = 0.55 + 0.45 * Math.sin(time * 4);
    g.circle(vx, vy, size + 6 + pulse * 2);
    g.stroke({ width: 2.5, color: 0xffffff, alpha: 0.75 + pulse * 0.25 });
  }
}

export function WorldCanvas() {
  const containerRef = useRef<HTMLDivElement>(null);
  const appRef = useRef<Application | null>(null);
  const stageRef = useRef<Container | null>(null);
  const terrainBaseRef = useRef<Container | null>(null);
  const terrainGlowRef = useRef<Container | null>(null);
  const activityRef = useRef<Container | null>(null);
  const agentLayerRef = useRef<Container | null>(null);
  const camRef = useRef<CameraState>(createCamera());
  const visualsRef = useRef<Map<string, AgentVisual>>(new Map());
  const activityMarksRef = useRef<ActivityMark[]>([]);
  const worldSigRef = useRef<string>('');
  const timeRef = useRef(0);
  const panDragRef = useRef({ dragging: false, lastX: 0, lastY: 0 });
  const sizeRef = useRef({ w: 800, h: 600 });
  const [size, setSize] = useState({ w: 800, h: 600 });

  const world = useSimStore((s) => s.world);
  const agents = useSimStore((s) => s.agents);
  const events = useSimStore((s) => s.events);
  const selectedAgentId = useSimStore((s) => s.selectedAgentId);
  const setSelectedAgent = useSimStore((s) => s.setSelectedAgent);
  const fetchAgent = useSimStore((s) => s.fetchAgent);
  const showTrails = useSimStore((s) => s.showTrails);
  const showActivity = useSimStore((s) => s.showActivity);
  const focusMode = useSimStore((s) => s.focusMode);

  const worldRef = useRef(world);
  const agentsRef = useRef(agents);
  const eventsRef = useRef(events);
  const selectedRef = useRef(selectedAgentId);
  const trailsRef = useRef(showTrails);
  const activityOnRef = useRef(showActivity);
  const focusRef = useRef(focusMode);
  worldRef.current = world;
  agentsRef.current = agents;
  eventsRef.current = events;
  selectedRef.current = selectedAgentId;
  trailsRef.current = showTrails;
  activityOnRef.current = showActivity;
  focusRef.current = focusMode;

  // Responsive sizing
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (!entry) return;
      const w = Math.max(320, Math.floor(entry.contentRect.width));
      const h = Math.max(280, Math.floor(entry.contentRect.height));
      sizeRef.current = { w, h };
      setSize({ w, h });
      if (appRef.current) {
        appRef.current.renderer.resize(w, h);
        if (worldRef.current) {
          fitCameraToWorld(camRef.current, worldRef.current.width, worldRef.current.height, w, h);
        }
      }
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // Sync agent visuals when agent snapshots change
  useEffect(() => {
    const map = visualsRef.current;
    const seen = new Set<string>();
    for (const a of agents) {
      seen.add(a.id);
      let v = map.get(a.id);
      if (!v) {
        v = createAgentVisual(a.id, a.x, a.y, a.current_task);
        map.set(a.id, v);
      } else {
        syncAgentVisual(v, a.x, a.y, a.current_task);
      }
    }
    for (const id of [...map.keys()]) {
      if (!seen.has(id)) map.delete(id);
    }
  }, [agents]);

  // Activity heat from recent events
  useEffect(() => {
    const marks = activityMarksRef.current;
    for (const e of events.slice(0, 40)) {
      if (!e.location) continue;
      if (e.event_type !== 'mine' && e.event_type !== 'harvest' && e.event_type !== 'recharge' && e.event_type !== 'death') {
        continue;
      }
      const [x, y] = e.location;
      const exists = marks.some((m) => m.x === x && m.y === y && m.kind === e.event_type && m.age < 0.3);
      if (!exists) marks.push({ x, y, kind: e.event_type, age: 0 });
    }
    if (marks.length > 200) marks.splice(0, marks.length - 200);
  }, [events]);

  // Focus camera on selection
  useEffect(() => {
    if (!selectedAgentId || !world) return;
    const agent = agents.find((a) => a.id === selectedAgentId);
    if (!agent) return;
    focusOnCell(camRef.current, agent.x, agent.y, sizeRef.current.w, sizeRef.current.h);
  }, [selectedAgentId, agents, world]);

  const rebuildTerrain = useCallback((wstate: WorldState, time: number) => {
    const baseC = terrainBaseRef.current;
    const glowC = terrainGlowRef.current;
    if (!baseC || !glowC) return;
    baseC.removeChildren();
    glowC.removeChildren();
    const { base, glow } = buildTerrainLayers(wstate, time);
    baseC.addChild(base);
    glowC.addChild(glow);
  }, []);

  useEffect(() => {
    if (!containerRef.current) return;
    let destroyed = false;
    let tickerFn: ((ticker: { deltaMS: number }) => void) | null = null;

    const onMouseUp = () => {
      panDragRef.current.dragging = false;
    };
    const onMouseMove = (e: MouseEvent) => {
      if (!panDragRef.current.dragging) return;
      const dx = e.clientX - panDragRef.current.lastX;
      const dy = e.clientY - panDragRef.current.lastY;
      panDragRef.current.lastX = e.clientX;
      panDragRef.current.lastY = e.clientY;
      const cam = camRef.current;
      cam.x += dx;
      cam.y += dy;
      cam.targetX = cam.x;
      cam.targetY = cam.y;
    };

    const init = async () => {
      const app = new Application();
      await app.init({
        width: sizeRef.current.w,
        height: sizeRef.current.h,
        backgroundColor: 0x03060c,
        antialias: true,
        resolution: Math.min(window.devicePixelRatio || 1, 2),
        autoDensity: true,
      });
      if (destroyed || !containerRef.current) {
        app.destroy();
        return;
      }
      containerRef.current.innerHTML = '';
      containerRef.current.appendChild(app.canvas);
      appRef.current = app;

      const stage = new Container();
      app.stage.addChild(stage);
      stageRef.current = stage;

      const ambient = new Graphics();
      for (let i = 0; i < 40; i++) {
        ambient.circle(Math.random() * 2000, Math.random() * 2000, Math.random() * 1.5 + 0.3);
        ambient.fill({ color: 0x4b6b8a, alpha: 0.15 + Math.random() * 0.2 });
      }
      stage.addChild(ambient);

      const terrainBase = new Container();
      const terrainGlow = new Container();
      const activity = new Container();
      const agentsLayer = new Container();
      stage.addChild(terrainBase);
      stage.addChild(terrainGlow);
      stage.addChild(activity);
      stage.addChild(agentsLayer);
      terrainBaseRef.current = terrainBase;
      terrainGlowRef.current = terrainGlow;
      activityRef.current = activity;
      agentLayerRef.current = agentsLayer;

      app.canvas.addEventListener('mousedown', (e) => {
        panDragRef.current.dragging = true;
        panDragRef.current.lastX = e.clientX;
        panDragRef.current.lastY = e.clientY;
      });
      window.addEventListener('mouseup', onMouseUp);
      window.addEventListener('mousemove', onMouseMove);
      app.canvas.addEventListener(
        'wheel',
        (e) => {
          e.preventDefault();
          const cam = camRef.current;
          const factor = e.deltaY > 0 ? 0.92 : 1.08;
          cam.targetZoom = Math.max(0.35, Math.min(4, cam.targetZoom * factor));
          cam.zoom = cam.targetZoom;
        },
        { passive: false },
      );

      if (worldRef.current) {
        fitCameraToWorld(
          camRef.current,
          worldRef.current.width,
          worldRef.current.height,
          sizeRef.current.w,
          sizeRef.current.h,
        );
        rebuildTerrain(worldRef.current, 0);
        worldSigRef.current = `${worldRef.current.width}x${worldRef.current.height}`;
      }

      tickerFn = (ticker) => {
        const dt = Math.min(0.05, ticker.deltaMS / 1000);
        timeRef.current += dt;
        const time = timeRef.current;
        const cam = camRef.current;
        easeCamera(cam, dt);
        stage.position.set(cam.x, cam.y);
        stage.scale.set(cam.zoom);

        const wstate = worldRef.current;
        if (wstate && terrainGlowRef.current) {
          terrainGlowRef.current.alpha = 0.75 + 0.25 * Math.sin(time * 2.1);
        }

        // Activity layer
        const actC = activityRef.current;
        if (actC) {
          actC.removeChildren();
          if (activityOnRef.current) {
            const g = new Graphics();
            const marks = activityMarksRef.current;
            for (const m of marks) {
              m.age += dt;
              const fade = Math.max(0, 1 - m.age / 4);
              if (fade <= 0) continue;
              const color =
                m.kind === 'mine' ? 0xfbbf24 : m.kind === 'death' ? 0xef4444 : 0x22d3ee;
              const cx = m.x * CELL + CELL / 2;
              const cy = m.y * CELL + CELL / 2;
              g.circle(cx, cy, CELL * (0.8 + (1 - fade)));
              g.fill({ color, alpha: 0.2 * fade });
            }
            activityMarksRef.current = marks.filter((m) => m.age < 4);
            actC.addChild(g);
          }
        }

        // Agents
        const layer = agentLayerRef.current;
        if (layer) {
          layer.removeChildren();
          const g = new Graphics();
          const list = agentsRef.current;
          const selected = selectedRef.current;
          const focus = focusRef.current && !!selected;
          const showIntent = trailsRef.current;

          for (const agent of list) {
            let visual = visualsRef.current.get(agent.id);
            if (!visual) {
              visual = createAgentVisual(agent.id, agent.x, agent.y, agent.current_task);
              visualsRef.current.set(agent.id, visual);
            }
            tickAgentVisual(visual, dt);
            if (!trailsRef.current) visual.trail = [];

            const vx = visual.displayX * CELL + CELL / 2;
            const vy = visual.displayY * CELL + CELL / 2;
            const dimmed = focus && agent.id !== selected;
            drawAgentBody(g, agent, vx, vy, visual, agent.id === selected, dimmed, showIntent, time);

            // Hit area proxy — use separate interactive graphics for clicks
          }
          layer.addChild(g);

          // Interactive hit targets (lightweight)
          for (const agent of list) {
            const visual = visualsRef.current.get(agent.id);
            if (!visual) continue;
            const hit = new Graphics();
            const vx = visual.displayX * CELL + CELL / 2;
            const vy = visual.displayY * CELL + CELL / 2;
            const size = 4 + agent.hardware.chassis_size * 2.4;
            hit.circle(vx, vy, size + 4);
            hit.fill({ color: 0xffffff, alpha: 0.001 });
            hit.eventMode = 'static';
            hit.cursor = 'pointer';
            hit.on('pointerdown', (ev) => {
              ev.stopPropagation();
              setSelectedAgent(agent.id);
              fetchAgent(agent.id);
            });
            layer.addChild(hit);
          }
        }
      };

      app.ticker.add(tickerFn);
    };

    init();
    return () => {
      destroyed = true;
      window.removeEventListener('mouseup', onMouseUp);
      window.removeEventListener('mousemove', onMouseMove);
      if (appRef.current && tickerFn) appRef.current.ticker.remove(tickerFn);
      appRef.current?.destroy(true);
      appRef.current = null;
      stageRef.current = null;
      terrainBaseRef.current = null;
      terrainGlowRef.current = null;
      activityRef.current = null;
      agentLayerRef.current = null;
    };
  }, [rebuildTerrain, setSelectedAgent, fetchAgent]);

  // Fit + rebuild terrain when world arrives / resets
  useEffect(() => {
    if (!world || !appRef.current) return;
    fitCameraToWorld(camRef.current, world.width, world.height, size.w, size.h);
    rebuildTerrain(world, timeRef.current);
    worldSigRef.current = `${world.width}x${world.height}`;
  }, [world, size.w, size.h, rebuildTerrain]);

  return <div ref={containerRef} className="world-canvas" />;
}
