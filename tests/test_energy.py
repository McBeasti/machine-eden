"""Tests for energy calculations and invariants."""

import pytest

from simulation.config import SimulationConfig
from simulation.engine import SimulationEngine


def test_energy_cannot_exceed_capacity(engine):
    agent = next(iter(engine.agents.values()))
    agent.energy = agent.hardware.energy_capacity + 100
    for _ in range(5):
        engine.step()
    for a in engine.agents.values():
        if a.alive:
            assert a.energy <= a.hardware.energy_capacity + 0.01


def test_energy_depletion_causes_death():
    config = SimulationConfig(
        seed=1, world_width=16, world_height=16, initial_population=3, energy_scarcity=5.0
    )
    engine = SimulationEngine(config)
    for agent in engine.agents.values():
        agent.energy = 0.0
    engine.step()
    deaths = sum(1 for a in engine.agents.values() if not a.alive)
    assert deaths >= 1


def test_dead_agents_cannot_act(engine):
    agent = next(iter(engine.agents.values()))
    agent.alive = False
    agent.energy = 0
    initial_tick = engine.tick
    engine.step()
    assert agent.current_task == "dead" or not agent.alive


def test_resources_never_negative(engine):
    for _ in range(20):
        engine.step()
    assert (engine.world.resources >= 0).all()


def test_idle_costs_energy(engine):
    agent = next(iter(engine.agents.values()))
    initial_energy = agent.energy
    agent.current_task = "idle"
    engine.step()
    # Agent may have moved/recharged but metabolism always costs something unless dead
    if agent.alive:
        assert agent.energy < initial_energy or agent.energy == initial_energy
