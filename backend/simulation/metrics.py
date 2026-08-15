"""Aggregated simulation metrics for analytics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class TickMetrics:
    tick: int
    population: int = 0
    births: int = 0
    deaths: int = 0
    mean_energy: float = 0.0
    mean_age: float = 0.0
    total_stored_resources: float = 0.0
    world_resource_total: float = 0.0
    mining_rate: float = 0.0
    energy_production: float = 0.0
    energy_consumption: float = 0.0
    mean_lifespan_deaths: float = 0.0
    territorial_concentration: float = 0.0
    genetic_diversity: float = 0.0
    idle_fraction: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in self.__dict__.items()}


@dataclass
class MetricsCollector:
    """Collects per-tick and cumulative metrics."""

    history: list[TickMetrics] = field(default_factory=list)
    cumulative_births: int = 0
    cumulative_deaths: int = 0
    cumulative_mining: float = 0.0
    death_ages: list[float] = field(default_factory=list)
    _last_mining: float = 0.0
    _tick_energy_produced: float = 0.0
    _tick_energy_consumed: float = 0.0

    def reset_tick_counters(self) -> None:
        self._tick_energy_produced = 0.0
        self._tick_energy_consumed = 0.0

    def record_energy_produced(self, amount: float) -> None:
        self._tick_energy_produced += amount

    def record_energy_consumed(self, amount: float) -> None:
        self._tick_energy_consumed += amount

    def record_mining(self, amount: float) -> None:
        self.cumulative_mining += amount
        self._last_mining = amount

    def record_death(self, age: int) -> None:
        self.cumulative_deaths += 1
        self.death_ages.append(float(age))

    def record_birth(self) -> None:
        self.cumulative_births += 1

    def compute(
        self,
        tick: int,
        agents: dict,
        world_resources: np.ndarray,
        births_this_tick: int = 0,
        deaths_this_tick: int = 0,
    ) -> TickMetrics:
        alive = [a for a in agents.values() if a.alive]
        pop = len(alive)

        mean_energy = float(np.mean([a.energy_ratio for a in alive])) if alive else 0.0
        mean_age = float(np.mean([a.age for a in alive])) if alive else 0.0
        stored = sum(a.inventory_total for a in alive)
        world_total = float(world_resources.sum())
        idle_count = sum(1 for a in alive if a.current_task == "idle")

        concentration = 0.0
        if pop > 1:
            xs = [a.x for a in alive]
            ys = [a.y for a in alive]
            spread = np.std(xs) + np.std(ys)
            concentration = 1.0 / (1.0 + spread * 0.1)

        lineages = {a.lineage_id for a in alive}
        diversity = len(lineages) / pop if pop > 0 else 0.0

        mean_lifespan = float(np.mean(self.death_ages)) if self.death_ages else 0.0

        m = TickMetrics(
            tick=tick,
            population=pop,
            births=births_this_tick,
            deaths=deaths_this_tick,
            mean_energy=mean_energy,
            mean_age=mean_age,
            total_stored_resources=stored,
            world_resource_total=world_total,
            mining_rate=self._last_mining,
            energy_production=self._tick_energy_produced,
            energy_consumption=self._tick_energy_consumed,
            mean_lifespan_deaths=mean_lifespan,
            territorial_concentration=concentration,
            genetic_diversity=diversity,
            idle_fraction=idle_count / pop if pop > 0 else 0.0,
        )
        self.history.append(m)
        self._last_mining = 0.0
        return m

    def get_history(self, last_n: int | None = None) -> list[dict]:
        hist = self.history[-last_n:] if last_n else self.history
        return [m.to_dict() for m in hist]

    def clear(self) -> None:
        self.history.clear()
        self.cumulative_births = 0
        self.cumulative_deaths = 0
        self.cumulative_mining = 0.0
        self.death_ages.clear()
