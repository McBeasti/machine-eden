import { useEffect, useRef, useCallback } from 'react';
import { Application, Container, Graphics } from 'pixi.js';
import { useSimStore } from '../store';
import { TERRAIN_COLORS } from '../types';
import type { Agent } from '../types';

const CELL = 6;

function lineageColor(lineageId: string): number {
  let hash = 0;
  for (let i = 0; i < lineageId.length; i++) {
    hash = lineageId.charCodeAt(i) + ((hash << 5) - hash);
  }
  const r = (hash & 0xff0000) >> 16;
  const g = (hash & 0x00ff00) >> 8;
  const b = hash & 0x0000ff;
  return (Math.min(255, r + 80) << 16) | (Math.min(255, g + 80) << 8) | Math.min(255, b + 80);
}

interface WorldCanvasProps {
  width: number;
  height: number;
}

export function WorldCanvas({ width, height }: WorldCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const appRef = useRef<Application | null>(null);
  const worldContainerRef = useRef<Container | null>(null);
  const agentContainerRef = useRef<Container | null>(null);
  const readyRef = useRef(false);
  const panRef = useRef({ x: 0, y: 0, dragging: false, lastX: 0, lastY: 0 });
  const zoomRef = useRef(1);

  const world = useSimStore((s) => s.world);
  const agents = useSimStore((s) => s.agents);
  const selectedAgentId = useSimStore((s) => s.selectedAgentId);
  const setSelectedAgent = useSimStore((s) => s.setSelectedAgent);
  const fetchAgent = useSimStore((s) => s.fetchAgent);

  const drawWorld = useCallback(() => {
    const app = appRef.current;
    const wc = worldContainerRef.current;
    if (!app || !wc || !world) return;

    wc.removeChildren();
    const g = new Graphics();
    const w = world.width;
    const h = world.height;

    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const terrain = world.terrain[y][x];
        const resource = world.resources[y][x];
        const color = TERRAIN_COLORS[terrain] ?? '#111';
        if (resource > 0 && terrain !== 0) {
          const alpha = Math.min(1, resource / 50);
          g.rect(x * CELL, y * CELL, CELL, CELL);
          g.fill({ color, alpha: 0.4 + alpha * 0.6 });
        } else {
          g.rect(x * CELL, y * CELL, CELL, CELL);
          g.fill(color);
        }
      }
    }
    wc.addChild(g);
  }, [world]);

  const drawAgents = useCallback(() => {
    const ac = agentContainerRef.current;
    if (!ac) return;
    ac.removeChildren();

    agents.forEach((agent: Agent) => {
      const g = new Graphics();
      const size = 3 + agent.hardware.chassis_size * 2;
      const color = lineageColor(agent.lineage_id);
      const ex = agent.x * CELL + CELL / 2;
      const ey = agent.y * CELL + CELL / 2;

      g.circle(ex, ey, size + 2);
      g.stroke({ width: 1, color: 0x00ff88, alpha: agent.energy_ratio * 0.8 });

      g.circle(ex, ey, size);
      g.fill(color);

      if (agent.id === selectedAgentId) {
        g.circle(ex, ey, size + 4);
        g.stroke({ width: 2, color: 0xffffff });
      }

      g.eventMode = 'static';
      g.cursor = 'pointer';
      g.on('pointerdown', () => {
        setSelectedAgent(agent.id);
        fetchAgent(agent.id);
      });

      ac.addChild(g);
    });
  }, [agents, selectedAgentId, setSelectedAgent, fetchAgent]);

  const drawWorldRef = useRef(drawWorld);
  const drawAgentsRef = useRef(drawAgents);
  drawWorldRef.current = drawWorld;
  drawAgentsRef.current = drawAgents;

  useEffect(() => {
    if (!containerRef.current) return;
    let destroyed = false;

    const onMouseUp = () => {
      panRef.current.dragging = false;
    };
    const onMouseMove = (e: MouseEvent) => {
      if (!panRef.current.dragging || !appRef.current) return;
      const stage = appRef.current.stage.children[0] as Container | undefined;
      if (!stage) return;
      const dx = e.clientX - panRef.current.lastX;
      const dy = e.clientY - panRef.current.lastY;
      panRef.current.x += dx;
      panRef.current.y += dy;
      panRef.current.lastX = e.clientX;
      panRef.current.lastY = e.clientY;
      stage.position.set(panRef.current.x, panRef.current.y);
    };

    const init = async () => {
      const app = new Application();
      await app.init({
        width,
        height,
        backgroundColor: 0x050810,
        antialias: true,
        resolution: window.devicePixelRatio,
        autoDensity: true,
      });
      if (destroyed) {
        app.destroy();
        return;
      }
      if (!containerRef.current) {
        app.destroy();
        return;
      }
      containerRef.current.appendChild(app.canvas);
      appRef.current = app;

      const stage = new Container();
      app.stage.addChild(stage);

      const worldC = new Container();
      const agentC = new Container();
      stage.addChild(worldC);
      stage.addChild(agentC);
      worldContainerRef.current = worldC;
      agentContainerRef.current = agentC;
      readyRef.current = true;

      app.canvas.addEventListener('mousedown', (e) => {
        panRef.current.dragging = true;
        panRef.current.lastX = e.clientX;
        panRef.current.lastY = e.clientY;
      });
      window.addEventListener('mouseup', onMouseUp);
      window.addEventListener('mousemove', onMouseMove);

      app.canvas.addEventListener('wheel', (e) => {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        zoomRef.current = Math.max(0.3, Math.min(4, zoomRef.current * delta));
        stage.scale.set(zoomRef.current);
      });

      // World/agents may already be loaded before Pixi finished initializing.
      drawWorldRef.current();
      drawAgentsRef.current();
    };

    init();
    return () => {
      destroyed = true;
      readyRef.current = false;
      window.removeEventListener('mouseup', onMouseUp);
      window.removeEventListener('mousemove', onMouseMove);
      appRef.current?.destroy(true);
      appRef.current = null;
      worldContainerRef.current = null;
      agentContainerRef.current = null;
    };
  }, [width, height]);

  useEffect(() => {
    if (readyRef.current) drawWorld();
  }, [drawWorld]);

  useEffect(() => {
    if (readyRef.current) drawAgents();
  }, [drawAgents]);

  return (
    <div
      ref={containerRef}
      style={{ width, height, borderRadius: 8, overflow: 'hidden', cursor: 'grab' }}
    />
  );
}
