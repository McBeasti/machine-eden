"""Action definitions, costs, and validation."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from simulation.agent import Agent
    from simulation.world import World


class ActionType(str, Enum):
    IDLE = "idle"
    MOVE = "move"
    SCAN = "scan"
    MINE = "mine"
    HARVEST = "harvest"
    RECHARGE = "recharge"
    COLLECT = "collect"


ENERGY_COSTS: dict[ActionType, float] = {
    ActionType.IDLE: 0.05,
    ActionType.MOVE: 0.5,
    ActionType.SCAN: 0.2,
    ActionType.MINE: 1.5,
    ActionType.HARVEST: 0.3,
    ActionType.RECHARGE: 0.1,
    ActionType.COLLECT: 0.2,
}

MOVE_ENERGY_PER_CELL = 0.3
RECHARGE_RATE = 15.0
HARVEST_RATE = 3.0
MINE_BASE_YIELD = 2.0
IDLE_COST_MULTIPLIER = 1.0


def move_cost(distance: float, movement_cost: float, energy_scarcity: float) -> float:
    return (MOVE_ENERGY_PER_CELL * distance * movement_cost + ENERGY_COSTS[ActionType.MOVE]) * energy_scarcity


def can_mine(agent: Agent, world: World) -> bool:
    from simulation.world import TerrainType

    if agent.hardware.mining_ability <= 0:
        return False
    terrain = world.get_terrain(agent.x, agent.y)
    if terrain not in (TerrainType.MINERAL, TerrainType.METAL, TerrainType.RARE, TerrainType.ABANDONED):
        return False
    return world.resources[agent.y, agent.x] > 0.5


def can_harvest(agent: Agent, world: World) -> bool:
    from simulation.world import TerrainType

    return world.get_terrain(agent.x, agent.y) == TerrainType.ENERGY_SOURCE


def can_recharge(agent: Agent, world: World) -> bool:
    from simulation.world import TerrainType

    return world.get_terrain(agent.x, agent.y) == TerrainType.CHARGING_STATION


def mine_yield(agent: Agent, world: World) -> float:
    """Calculate mining yield based on ability and remaining resources."""
    available = float(world.resources[agent.y, agent.x])
    ability = agent.hardware.mining_ability
    return min(MINE_BASE_YIELD * ability, available)
