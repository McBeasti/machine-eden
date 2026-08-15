"""Tests for event logging."""

from simulation.config import SimulationConfig
from simulation.engine import SimulationEngine


def test_spawn_events_on_reset():
    engine = SimulationEngine(SimulationConfig(seed=1, initial_population=5, world_width=16, world_height=16))
    types = [e.event_type for e in engine.events._all_events]
    assert types.count("spawn") == 5


def test_events_have_tick():
    engine = SimulationEngine(SimulationConfig(seed=2, initial_population=3, world_width=16, world_height=16))
    engine.step()
    for e in engine.events._all_events:
        assert e.tick >= 0


def test_death_events_logged():
    config = SimulationConfig(seed=4, initial_population=2, world_width=16, world_height=16, energy_scarcity=5.0)
    engine = SimulationEngine(config)
    for a in engine.agents.values():
        a.energy = 0.0
    engine.step()
    types = [e.event_type for e in engine.events._all_events]
    assert "death" in types
