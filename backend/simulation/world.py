"""World terrain types and grid state."""

from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.random import Generator

    from simulation.config import SimulationConfig


class TerrainType(IntEnum):
    EMPTY = 0
    MINERAL = 1
    METAL = 2
    RARE = 3
    ENERGY_SOURCE = 4
    CHARGING_STATION = 5
    HAZARD = 6
    ABANDONED = 7


TERRAIN_NAMES = {t.value: t.name.lower() for t in TerrainType}

REGEN_RATES: dict[TerrainType, float] = {
    TerrainType.MINERAL: 1.0,
    TerrainType.ENERGY_SOURCE: 1.0,
    TerrainType.METAL: 0.0,
    TerrainType.RARE: 0.0,
    TerrainType.CHARGING_STATION: 0.0,
    TerrainType.HAZARD: 0.0,
    TerrainType.ABANDONED: 0.0,
    TerrainType.EMPTY: 0.0,
}


class World:
    """2D grid world with resource and terrain state stored in NumPy arrays."""

    def __init__(self, config: SimulationConfig, rng: Generator) -> None:
        self.width = config.world_width
        self.height = config.world_height
        self.config = config

        self.terrain = np.zeros((self.height, self.width), dtype=np.int8)
        self.resources = np.zeros((self.height, self.width), dtype=np.float32)
        self.max_resources = np.zeros((self.height, self.width), dtype=np.float32)
        self.movement_cost = np.ones((self.height, self.width), dtype=np.float32)
        self.hazard_level = np.zeros((self.height, self.width), dtype=np.float32)
        self.signal_quality = np.ones((self.height, self.width), dtype=np.float32)

        self._generate(rng)

    def _generate(self, rng: Generator) -> None:
        """Procedurally generate terrain and resources from seed."""
        cfg = self.config
        total_cells = self.width * self.height

        mineral_mask = rng.random((self.height, self.width)) < cfg.resource_density
        self.terrain[mineral_mask] = TerrainType.MINERAL
        quantities = rng.uniform(20, 80, size=(self.height, self.width)).astype(np.float32)
        self.resources[mineral_mask] = quantities[mineral_mask]
        self.max_resources[mineral_mask] = self.resources[mineral_mask].copy()

        metal_candidates = (self.terrain == TerrainType.EMPTY) & (
            rng.random((self.height, self.width)) < cfg.resource_density * 0.4
        )
        self.terrain[metal_candidates] = TerrainType.METAL
        metal_qty = rng.uniform(10, 40, size=(self.height, self.width)).astype(np.float32)
        self.resources[metal_candidates] = metal_qty[metal_candidates]
        self.max_resources[metal_candidates] = self.resources[metal_candidates].copy()

        energy_count = max(1, int(total_cells * cfg.energy_source_density))
        self._place_features(rng, TerrainType.ENERGY_SOURCE, energy_count, 30.0, 60.0)

        station_count = max(2, int(total_cells * cfg.charging_station_density))
        self._place_features(rng, TerrainType.CHARGING_STATION, station_count, 0.0, 0.0)

        hazard_count = max(0, int(total_cells * cfg.hazard_density))
        if hazard_count > 0:
            self._place_features(rng, TerrainType.HAZARD, hazard_count, 0.0, 0.0)
            hazard_mask = self.terrain == TerrainType.HAZARD
            self.hazard_level[hazard_mask] = rng.uniform(0.3, 1.0, size=int(hazard_mask.sum()))
            self.movement_cost[hazard_mask] = rng.uniform(1.5, 3.0, size=int(hazard_mask.sum()))
            self.signal_quality[hazard_mask] = rng.uniform(0.1, 0.5, size=int(hazard_mask.sum()))

        abandoned_count = max(1, int(total_cells * 0.005))
        self._place_features(rng, TerrainType.ABANDONED, abandoned_count, 5.0, 15.0)

        noise = rng.random((self.height, self.width)).astype(np.float32)
        self.signal_quality *= 0.7 + 0.3 * noise

    def _place_features(
        self,
        rng: Generator,
        terrain: TerrainType,
        count: int,
        qty_min: float,
        qty_max: float,
    ) -> None:
        empty_cells = np.argwhere(self.terrain == TerrainType.EMPTY)
        if len(empty_cells) == 0:
            return
        count = min(count, len(empty_cells))
        indices = rng.choice(len(empty_cells), size=count, replace=False)
        for idx in indices:
            y, x = empty_cells[idx]
            self.terrain[y, x] = terrain
            if qty_max > 0:
                qty = rng.uniform(qty_min, qty_max)
                self.resources[y, x] = qty
                self.max_resources[y, x] = qty

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get_terrain(self, x: int, y: int) -> TerrainType:
        return TerrainType(int(self.terrain[y, x]))

    def regenerate(self, rng: Generator) -> list[tuple[int, int, float]]:
        """Regenerate renewable resources. Returns list of (x, y, amount)."""
        cfg = self.config
        events: list[tuple[int, int, float]] = []
        rate = cfg.renewable_rate

        for terrain_type in (TerrainType.MINERAL, TerrainType.ENERGY_SOURCE):
            mask = self.terrain == terrain_type
            if not mask.any():
                continue
            regen = rate * REGEN_RATES[terrain_type] * self.max_resources[mask]
            regen *= 1.0 + rng.uniform(-0.1, 0.1, size=regen.shape)
            current = self.resources[mask]
            new_vals = np.minimum(current + regen, self.max_resources[mask])
            delta = new_vals - current
            self.resources[mask] = new_vals

            positions = np.argwhere(mask)
            for i, (y, x) in enumerate(positions):
                if delta[i] > 0.01:
                    events.append((int(x), int(y), float(delta[i])))

        return events

    def to_dict(self) -> dict:
        """Serialize world for API (downsampled for bandwidth)."""
        return {
            "width": self.width,
            "height": self.height,
            "terrain": self.terrain.tolist(),
            "resources": self.resources.tolist(),
        }

    def cell_summary(self, x: int, y: int) -> dict:
        t = self.get_terrain(x, y)
        return {
            "x": x,
            "y": y,
            "terrain": TERRAIN_NAMES[t.value],
            "resource": float(self.resources[y, x]),
            "max_resource": float(self.max_resources[y, x]),
            "movement_cost": float(self.movement_cost[y, x]),
            "hazard_level": float(self.hazard_level[y, x]),
            "signal_quality": float(self.signal_quality[y, x]),
        }
