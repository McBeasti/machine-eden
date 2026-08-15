"""Agent identity, hardware, and internal state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from numpy.random import Generator


@dataclass
class Hardware:
    """Physical machine characteristics."""

    chassis_size: float = 1.0
    movement_speed: float = 2.0
    carrying_capacity: float = 10.0
    armour: float = 0.0
    sensor_range: float = 5.0
    communication_range: float = 8.0
    energy_capacity: float = 100.0
    energy_consumption: float = 0.1
    mining_ability: float = 0.5
    construction_ability: float = 0.0
    manufacturing_ability: float = 0.0
    attack_power: float = 0.0
    repair_ability: float = 0.0
    processing_capacity: float = 1.0

    def to_dict(self) -> dict[str, float]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


@dataclass
class Software:
    """Behavioural parameters (Phase 1 defaults, mutated in Phase 2)."""

    cooperation_tendency: float = 0.5
    aggression_tendency: float = 0.2
    exploration_tendency: float = 0.5
    risk_tolerance: float = 0.5
    resource_sharing_tendency: float = 0.3
    loyalty_tendency: float = 0.5
    mutation_rate: float = 0.05
    communication_protocol_version: int = 1

    def to_dict(self) -> dict[str, float | int]:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


@dataclass
class Agent:
    """Autonomous machine agent."""

    id: str
    x: int
    y: int
    generation: int = 0
    parent_ids: list[str] = field(default_factory=list)
    lineage_id: str = ""
    created_tick: int = 0
    age: int = 0
    colony_id: str | None = None
    role: str | None = None

    hardware: Hardware = field(default_factory=Hardware)
    software: Software = field(default_factory=Software)

    energy: float = 80.0
    damage: float = 0.0
    inventory: dict[str, float] = field(default_factory=dict)
    current_task: str = "idle"

    visit_map: dict[tuple[int, int], int] = field(default_factory=dict)

    alive: bool = True

    def __post_init__(self) -> None:
        if not self.lineage_id:
            self.lineage_id = self.id

    @property
    def inventory_total(self) -> float:
        return sum(self.inventory.values())

    @property
    def energy_ratio(self) -> float:
        cap = self.hardware.energy_capacity
        return self.energy / cap if cap > 0 else 0.0

    def can_carry(self, amount: float) -> bool:
        return self.inventory_total + amount <= self.hardware.carrying_capacity

    def add_to_inventory(self, resource_type: str, amount: float) -> float:
        """Add resources up to capacity. Returns amount actually added."""
        space = self.hardware.carrying_capacity - self.inventory_total
        added = min(amount, space)
        if added > 0:
            self.inventory[resource_type] = self.inventory.get(resource_type, 0) + added
        return added

    def spend_energy(self, amount: float) -> bool:
        """Deduct energy. Returns False if insufficient."""
        if self.energy < amount:
            return False
        self.energy -= amount
        return True

    def clamp_energy(self) -> None:
        """Ensure energy stays within [0, capacity]."""
        self.energy = max(0.0, min(self.energy, self.hardware.energy_capacity))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "generation": self.generation,
            "parent_ids": self.parent_ids,
            "lineage_id": self.lineage_id,
            "created_tick": self.created_tick,
            "age": self.age,
            "colony_id": self.colony_id,
            "role": self.role,
            "hardware": self.hardware.to_dict(),
            "software": self.software.to_dict(),
            "energy": round(self.energy, 2),
            "damage": round(self.damage, 2),
            "inventory": dict(self.inventory),
            "current_task": self.current_task,
            "alive": self.alive,
            "energy_ratio": round(self.energy_ratio, 3),
        }


def create_agent(
    rng: Generator,
    x: int,
    y: int,
    tick: int = 0,
    generation: int = 0,
    parent_ids: list[str] | None = None,
    agent_index: int | None = None,
) -> Agent:
    """Create a new agent with randomized hardware."""
    id_bytes = rng.integers(0, 256, size=16, dtype=np.uint8)
    agent_id = "".join(f"{b:02x}" for b in id_bytes)

    hw = Hardware(
        chassis_size=rng.uniform(0.8, 1.5),
        movement_speed=rng.uniform(1.0, 3.0),
        carrying_capacity=rng.uniform(5.0, 20.0),
        sensor_range=rng.uniform(3.0, 8.0),
        communication_range=rng.uniform(5.0, 12.0),
        energy_capacity=rng.uniform(50.0, 150.0),
        energy_consumption=rng.uniform(0.08, 0.15),
        mining_ability=rng.uniform(0.1, 1.0),
        construction_ability=rng.uniform(0.0, 0.3),
        manufacturing_ability=rng.uniform(0.0, 0.2),
        attack_power=rng.uniform(0.0, 0.5),
        repair_ability=rng.uniform(0.0, 0.3),
    )
    sw = Software(
        cooperation_tendency=rng.uniform(0.2, 0.8),
        aggression_tendency=rng.uniform(0.0, 0.5),
        exploration_tendency=rng.uniform(0.3, 0.9),
        risk_tolerance=rng.uniform(0.2, 0.8),
        resource_sharing_tendency=rng.uniform(0.1, 0.6),
        loyalty_tendency=rng.uniform(0.2, 0.8),
    )
    energy = hw.energy_capacity * rng.uniform(0.5, 0.9)
    return Agent(
        id=agent_id,
        x=x,
        y=y,
        generation=generation,
        parent_ids=parent_ids or [],
        lineage_id=agent_id,
        created_tick=tick,
        hardware=hw,
        software=sw,
        energy=energy,
    )
