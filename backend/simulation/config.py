"""Simulation configuration and presets."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RewardProfile(str, Enum):
    INDIVIDUALISTIC = "individualistic"
    COOPERATIVE = "cooperative"
    COMPETITIVE = "competitive"
    MIXED = "mixed"


class SimulationConfig(BaseModel):
    """All tunable simulation parameters."""

    seed: int = 42
    world_width: int = Field(default=128, ge=8, le=512)
    world_height: int = Field(default=128, ge=8, le=512)
    initial_population: int = Field(default=80, ge=1, le=500)
    resource_density: float = Field(default=0.15, ge=0.01, le=0.5)
    renewable_rate: float = Field(default=0.002, ge=0.0, le=0.05)
    mutation_rate: float = Field(default=0.05, ge=0.0, le=0.5)
    environmental_danger: float = Field(default=0.1, ge=0.0, le=1.0)
    energy_scarcity: float = Field(default=1.0, ge=0.1, le=5.0)
    attack_cost: float = Field(default=5.0, ge=0.0)
    communication_cost: float = Field(default=0.5, ge=0.0)
    reproduction_cost: float = Field(default=50.0, ge=0.0)
    max_agents: int = Field(default=500, ge=10, le=5000)
    reward_profile: RewardProfile = RewardProfile.MIXED
    ticks_per_second: float = Field(default=10.0, ge=0.1, le=100.0)
    charging_station_density: float = Field(default=0.008, ge=0.001, le=0.05)
    energy_source_density: float = Field(default=0.02, ge=0.005, le=0.1)
    hazard_density: float = Field(default=0.03, ge=0.0, le=0.2)

    model_config = {"use_enum_values": True}


PRESETS: dict[str, dict[str, Any]] = {
    "resource_abundance": {
        "resource_density": 0.35,
        "renewable_rate": 0.01,
        "energy_scarcity": 0.5,
    },
    "energy_crisis": {
        "resource_density": 0.08,
        "energy_scarcity": 2.5,
        "charging_station_density": 0.003,
        "renewable_rate": 0.0005,
    },
    "high_mutation": {
        "mutation_rate": 0.15,
    },
    "hostile_world": {
        "environmental_danger": 0.8,
        "hazard_density": 0.12,
        "energy_scarcity": 1.5,
    },
    "cooperative_incentives": {
        "reward_profile": RewardProfile.COOPERATIVE,
    },
    "competitive_incentives": {
        "reward_profile": RewardProfile.COMPETITIVE,
    },
    "isolated_regions": {
        "world_width": 256,
        "world_height": 256,
        "resource_density": 0.08,
        "initial_population": 60,
    },
    "dense_megastructure": {
        "world_width": 64,
        "world_height": 64,
        "initial_population": 200,
        "resource_density": 0.25,
    },
}


def apply_preset(name: str, config: SimulationConfig) -> SimulationConfig:
    """Return a new config with preset overrides applied."""
    if name not in PRESETS:
        raise ValueError(f"Unknown preset: {name}")
    data = config.model_dump()
    data.update(PRESETS[name])
    return SimulationConfig(**data)
