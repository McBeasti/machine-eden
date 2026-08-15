/** Camera helpers for pan/zoom and fit-to-world. */

import { CELL } from './palette';

export interface CameraState {
  x: number;
  y: number;
  zoom: number;
  targetX: number;
  targetY: number;
  targetZoom: number;
}

export function createCamera(): CameraState {
  return { x: 0, y: 0, zoom: 1, targetX: 0, targetY: 0, targetZoom: 1 };
}

export function fitCameraToWorld(
  cam: CameraState,
  worldW: number,
  worldH: number,
  viewW: number,
  viewH: number,
  padding = 24,
): void {
  const worldPxW = worldW * CELL;
  const worldPxH = worldH * CELL;
  const zoom = Math.min((viewW - padding * 2) / worldPxW, (viewH - padding * 2) / worldPxH, 2.5);
  cam.zoom = zoom;
  cam.targetZoom = zoom;
  cam.x = (viewW - worldPxW * zoom) / 2;
  cam.y = (viewH - worldPxH * zoom) / 2;
  cam.targetX = cam.x;
  cam.targetY = cam.y;
}

export function easeCamera(cam: CameraState, dt: number): void {
  const k = 1 - Math.exp(-dt * 6);
  cam.x += (cam.targetX - cam.x) * k;
  cam.y += (cam.targetY - cam.y) * k;
  cam.zoom += (cam.targetZoom - cam.zoom) * k;
}

export function focusOnCell(
  cam: CameraState,
  cellX: number,
  cellY: number,
  viewW: number,
  viewH: number,
  zoom = Math.max(cam.zoom, 1.4),
): void {
  const px = cellX * CELL + CELL / 2;
  const py = cellY * CELL + CELL / 2;
  cam.targetZoom = Math.min(3.2, zoom);
  cam.targetX = viewW / 2 - px * cam.targetZoom;
  cam.targetY = viewH / 2 - py * cam.targetZoom;
}

export function worldToScreen(cam: CameraState, wx: number, wy: number): { x: number; y: number } {
  return { x: cam.x + wx * cam.zoom, y: cam.y + wy * cam.zoom };
}
