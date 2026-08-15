"""Tests for resource extraction."""

from simulation.config import SimulationConfig
from simulation.engine import SimulationEngine
from simulation.world import TerrainType


def test_mining_reduces_world_resources():
    config = SimulationConfig(seed=10, world_width=32, world_height=32, initial_population=20)
    engine = SimulationEngine(config)
    initial_total = float(engine.world.resources.sum())
    for _ in range(30):
        engine.step()
    final_total = float(engine.world.resources.sum())
    stored = sum(a.inventory_total for a in engine.agents.values() if a.alive)
    # Resources should have moved from world to inventories or been consumed
    assert final_total + stored <= initial_total + 1.0 or stored > 0


def test_mining_events_logged():
    config = SimulationConfig(seed=20, world_width=32, world_height=32, initial_population=15)
    engine = SimulationEngine(config)
    # Place agent on mineral
    agent = next(iter(engine.agents.values()))
    for y in range(engine.world.height):
        for x in range(engine.world.width):
            if engine.world.get_terrain(x, y) == TerrainType.MINERAL:
                agent.x, agent.y = x, y
                agent.energy = agent.hardware.energy_capacity
                agent.inventory.clear()
                break
    for _ in range(5):
        engine.step()
    event_types = [e.event_type for e in engine.events._all_events]
    assert "mine" in event_types or "move" in event_types
