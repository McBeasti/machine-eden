"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from simulation.config import SimulationConfig
from simulation.engine import SimulationEngine


@pytest.fixture
def default_config() -> SimulationConfig:
    return SimulationConfig(
        seed=42,
        world_width=32,
        world_height=32,
        initial_population=10,
        resource_density=0.2,
    )


@pytest.fixture
def engine(default_config: SimulationConfig) -> SimulationEngine:
    return SimulationEngine(default_config)
