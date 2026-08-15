"""Tests for movement and spatial rules."""

from simulation.config import SimulationConfig
from simulation.engine import SimulationEngine


def test_agents_move_over_ticks():
    config = SimulationConfig(seed=5, world_width=32, world_height=32, initial_population=5)
    engine = SimulationEngine(config)
    positions_before = {a.id: (a.x, a.y) for a in engine.agents.values()}
    for _ in range(10):
        engine.step()
    moved = 0
    for a in engine.agents.values():
        if a.alive and positions_before[a.id] != (a.x, a.y):
            moved += 1
    assert moved >= 1


def test_agents_stay_in_bounds():
    config = SimulationConfig(seed=3, world_width=16, world_height=16, initial_population=8)
    engine = SimulationEngine(config)
    for _ in range(50):
        engine.step()
        for a in engine.agents.values():
            if a.alive:
                assert 0 <= a.x < engine.world.width
                assert 0 <= a.y < engine.world.height
