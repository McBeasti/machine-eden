/** Living-colony colour system for terrain, tasks, and lineage. */

export const CELL = 8;

/** Stronger luminous terrain accents on near-black ground. */
export const TERRAIN_HEX: Record<number, number> = {
  0: 0x070b12,
  1: 0x1a7a52, // mineral
  2: 0x8a6a3a, // metal
  3: 0xa855f7, // rare
  4: 0xffc107, // energy
  5: 0x22d3ee, // charging
  6: 0xef4444, // hazard
  7: 0x64748b, // abandoned
};

export const TERRAIN_GLOW: Record<number, number> = {
  1: 0x34d399,
  2: 0xd4a574,
  3: 0xc084fc,
  4: 0xffe066,
  5: 0x67e8f9,
  6: 0xf87171,
  7: 0x94a3b8,
};

export const TASK_COLORS: Record<string, number> = {
  move: 0x38bdf8,
  explore: 0x38bdf8,
  mine: 0xfbbf24,
  harvest: 0xf59e0b,
  recharge: 0x22d3ee,
  idle: 0x64748b,
  dead: 0xef4444,
};

export const TASK_LABELS: Record<string, string> = {
  move: 'Move',
  explore: 'Explore',
  mine: 'Mine',
  harvest: 'Harvest',
  recharge: 'Charge',
  idle: 'Idle',
  dead: 'Dead',
};

export function lineageColor(lineageId: string): number {
  let hash = 0;
  for (let i = 0; i < lineageId.length; i++) {
    hash = lineageId.charCodeAt(i) + ((hash << 5) - hash);
  }
  const hue = ((hash % 360) + 360) % 360;
  return hslToHex(hue, 0.62, 0.58);
}

export function taskColor(task: string): number {
  return TASK_COLORS[task] ?? TASK_COLORS.idle;
}

export function hslToHex(h: number, s: number, l: number): number {
  const c = (1 - Math.abs(2 * l - 1)) * s;
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
  const m = l - c / 2;
  let r = 0;
  let g = 0;
  let b = 0;
  if (h < 60) [r, g, b] = [c, x, 0];
  else if (h < 120) [r, g, b] = [x, c, 0];
  else if (h < 180) [r, g, b] = [0, c, x];
  else if (h < 240) [r, g, b] = [0, x, c];
  else if (h < 300) [r, g, b] = [x, 0, c];
  else [r, g, b] = [c, 0, x];
  const R = Math.round((r + m) * 255);
  const G = Math.round((g + m) * 255);
  const B = Math.round((b + m) * 255);
  return (R << 16) | (G << 8) | B;
}

export function withAlpha(color: number, alpha: number): { color: number; alpha: number } {
  return { color, alpha: Math.max(0, Math.min(1, alpha)) };
}
