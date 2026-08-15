"""Tests for deterministic seeded simulation runs."""

from simulation.config import SimulationConfig
from simulation.engine import SimulationEngine


def _run_ticks(seed: int, ticks: int) -> dict:
    config = SimulationConfig(seed=seed, world_width=32, world_height=32, initial_population=15)
    engine = SimulationEngine(config)
    for _ in range(ticks):
        engine.step()
    alive = [a for a in engine.agents.values() if a.alive]
    return {
        "population": len(alive),
        "tick": engine.tick,
        "mean_energy": sum(a.energy for a in alive) / max(len(alive), 1),
        "world_resources": float(engine.world.resources.sum()),
    }


def test_same_seed_produces_same_results():
    r1 = _run_ticks(42, 50)
    r2 = _run_ticks(42, 50)
    assert r1 == r2


def test_different_seeds_differ():
    r1 = _run_ticks(42, 30)
    r2 = _run_ticks(99, 30)
    # At least one metric should differ
    assert r1["population"] != r2["population"] or r1["mean_energy"] != r2["mean_energy"]


def test_initial_world_is_deterministic():
    config = SimulationConfig(seed=7, world_width=16, world_height=16)
    e1 = SimulationEngine(config)
    e2 = SimulationEngine(config)
    assert e1.world.terrain.tolist() == e2.world.terrain.tolist()
    assert e1.world.resources.tolist() == e2.world.resources.tolist()
