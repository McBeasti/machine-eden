"""Spatial hash grid for efficient neighbor queries."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from simulation.agent import Agent


class SpatialIndex:
    """Grid-based spatial index for agents."""

    def __init__(self, cell_size: int = 8) -> None:
        self.cell_size = cell_size
        self._grid: dict[tuple[int, int], list[str]] = {}
        self._positions: dict[str, tuple[int, int]] = {}

    def _cell_key(self, x: int, y: int) -> tuple[int, int]:
        return (x // self.cell_size, y // self.cell_size)

    def clear(self) -> None:
        self._grid.clear()
        self._positions.clear()

    def insert(self, agent_id: str, x: int, y: int) -> None:
        key = self._cell_key(x, y)
        if agent_id in self._positions:
            self.remove(agent_id)
        self._positions[agent_id] = (x, y)
        self._grid.setdefault(key, []).append(agent_id)

    def remove(self, agent_id: str) -> None:
        if agent_id not in self._positions:
            return
        x, y = self._positions.pop(agent_id)
        key = self._cell_key(x, y)
        if key in self._grid:
            self._grid[key] = [a for a in self._grid[key] if a != agent_id]
            if not self._grid[key]:
                del self._grid[key]

    def update(self, agent_id: str, x: int, y: int) -> None:
        self.insert(agent_id, x, y)

    def query_radius(
        self, x: int, y: int, radius: float, agents: dict[str, Agent]
    ) -> list[Agent]:
        """Return all agents within radius of (x, y)."""
        cell_radius = int(radius // self.cell_size) + 1
        cx, cy = self._cell_key(x, y)
        result: list[Agent] = []
        r_sq = radius * radius

        for dx in range(-cell_radius, cell_radius + 1):
            for dy in range(-cell_radius, cell_radius + 1):
                key = (cx + dx, cy + dy)
                for aid in self._grid.get(key, []):
                    agent = agents.get(aid)
                    if agent and agent.alive:
                        dist_sq = (agent.x - x) ** 2 + (agent.y - y) ** 2
                        if dist_sq <= r_sq:
                            result.append(agent)
        return result

    def rebuild(self, agents: dict[str, Agent]) -> None:
        self.clear()
        for agent in agents.values():
            if agent.alive:
                self.insert(agent.id, agent.x, agent.y)
