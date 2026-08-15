/** Agent trail buffer for living-colony motion. */

export interface TrailPoint {
  x: number;
  y: number;
  age: number;
}

export interface AgentVisual {
  id: string;
  displayX: number;
  displayY: number;
  targetX: number;
  targetY: number;
  trail: TrailPoint[];
  flash: number;
  lastTask: string;
}

const TRAIL_MAX = 14;

export function createAgentVisual(id: string, x: number, y: number, task: string): AgentVisual {
  return {
    id,
    displayX: x,
    displayY: y,
    targetX: x,
    targetY: y,
    trail: [],
    flash: 0,
    lastTask: task,
  };
}

export function syncAgentVisual(v: AgentVisual, x: number, y: number, task: string): void {
  const moved = Math.hypot(x - v.targetX, y - v.targetY) > 0.01;
  if (moved) {
    v.trail.push({ x: v.displayX, y: v.displayY, age: 0 });
    if (v.trail.length > TRAIL_MAX) v.trail.shift();
  }
  if (task !== v.lastTask && (task === 'mine' || task === 'harvest' || task === 'recharge')) {
    v.flash = 1;
  }
  v.targetX = x;
  v.targetY = y;
  v.lastTask = task;
}

export function tickAgentVisual(v: AgentVisual, dt: number, lerpSpeed = 10): void {
  const k = 1 - Math.exp(-dt * lerpSpeed);
  v.displayX += (v.targetX - v.displayX) * k;
  v.displayY += (v.targetY - v.displayY) * k;
  v.flash = Math.max(0, v.flash - dt * 2.2);
  for (const p of v.trail) p.age += dt;
  v.trail = v.trail.filter((p) => p.age < 1.6);
}
