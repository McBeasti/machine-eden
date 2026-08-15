"""Phase 1 rule-based decision engine."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from simulation.actions import ActionType, can_harvest, can_mine, can_recharge
from simulation.decisions import DecisionRecord
from simulation.world import TerrainType

if TYPE_CHECKING:
    from simulation.agent import Agent
    from simulation.config import SimulationConfig
    from simulation.world import World


@dataclass
class ActionIntent:
    action: ActionType
    target_x: int | None = None
    target_y: int | None = None
    decision: DecisionRecord | None = None


def _distance(x1: int, y1: int, x2: int, y2: int) -> float:
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def _find_nearest_terrain(
    agent: Agent,
    world: World,
    terrain_types: set[TerrainType],
    max_range: float | None = None,
) -> tuple[int, int] | None:
    """Find nearest cell matching terrain types within sensor range."""
    r = int(max_range or agent.hardware.sensor_range)
    best_dist = float("inf")
    best_pos: tuple[int, int] | None = None

    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            nx, ny = agent.x + dx, agent.y + dy
            if not world.in_bounds(nx, ny):
                continue
            if world.get_terrain(nx, ny) not in terrain_types:
                continue
            if terrain_types & {TerrainType.MINERAL, TerrainType.METAL, TerrainType.RARE}:
                if world.resources[ny, nx] < 0.5:
                    continue
            d = _distance(agent.x, agent.y, nx, ny)
            if d < best_dist:
                best_dist = d
                best_pos = (nx, ny)
    return best_pos


def _find_nearest_resource_to_mine(agent: Agent, world: World) -> tuple[int, int] | None:
    mineable = {TerrainType.MINERAL, TerrainType.METAL, TerrainType.RARE, TerrainType.ABANDONED}
    return _find_nearest_terrain(agent, world, mineable)


def _step_toward(agent: Agent, target_x: int, target_y: int) -> tuple[int, int]:
    """Compute next cell moving toward target."""
    dx = target_x - agent.x
    dy = target_y - agent.y
    if dx == 0 and dy == 0:
        return agent.x, agent.y
    if abs(dx) >= abs(dy):
        step_x = agent.x + (1 if dx > 0 else -1)
        step_y = agent.y
    else:
        step_x = agent.x
        step_y = agent.y + (1 if dy > 0 else -1)
    return step_x, step_y


def _explore_direction(agent: Agent, world: World, rng) -> tuple[int, int]:
    """Move toward least-visited neighboring cell."""
    candidates: list[tuple[int, int, float]] = []
    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1)]:
        nx, ny = agent.x + dx, agent.y + dy
        if not world.in_bounds(nx, ny):
            continue
        visits = agent.visit_map.get((nx, ny), 0)
        score = visits + rng.uniform(0, agent.software.exploration_tendency * 3)
        candidates.append((nx, ny, score))
    if not candidates:
        return agent.x, agent.y
    candidates.sort(key=lambda c: c[2])
    return candidates[0][0], candidates[0][1]


def decide(
    agent: Agent,
    world: World,
    config: SimulationConfig,
    tick: int,
    rng,
) -> ActionIntent:
    """Rule-based priority decision tree."""
    energy_ratio = agent.energy_ratio
    inventory_ratio = agent.inventory_total / max(agent.hardware.carrying_capacity, 1.0)

    inputs = {
        "energy_ratio": round(energy_ratio, 3),
        "damage": agent.damage,
        "inventory_ratio": round(inventory_ratio, 3),
        "position": [agent.x, agent.y],
        "sensor_range": agent.hardware.sensor_range,
    }

    if can_recharge(agent, world) and energy_ratio < 0.95:
        decision = DecisionRecord(
            agent_id=agent.id,
            tick=tick,
            observed_inputs=inputs,
            selected_action=ActionType.RECHARGE.value,
            competing_actions=["move", "mine"],
            policy_scores={"recharge": 1.0, "move": 0.2},
            current_goal="restore_energy",
            interpretation="On charging station with room to recharge",
        )
        return ActionIntent(ActionType.RECHARGE, decision=decision)

    if can_harvest(agent, world) and energy_ratio < 0.85:
        decision = DecisionRecord(
            agent_id=agent.id,
            tick=tick,
            observed_inputs=inputs,
            selected_action=ActionType.HARVEST.value,
            competing_actions=["move"],
            policy_scores={"harvest": 0.9},
            current_goal="harvest_energy",
            interpretation="On energy source, harvesting passive energy",
        )
        return ActionIntent(ActionType.HARVEST, decision=decision)

    if energy_ratio < 0.25:
        station = _find_nearest_terrain(agent, world, {TerrainType.CHARGING_STATION})
        source = _find_nearest_terrain(agent, world, {TerrainType.ENERGY_SOURCE})
        target = station or source
        if target:
            tx, ty = _step_toward(agent, target[0], target[1])
            decision = DecisionRecord(
                agent_id=agent.id,
                tick=tick,
                observed_inputs=inputs,
                selected_action=ActionType.MOVE.value,
                competing_actions=["mine", "explore"],
                policy_scores={"seek_energy": 1.0, "mine": 0.1},
                current_goal="emergency_energy",
                interpretation=f"Critical energy ({energy_ratio:.0%}), moving toward power",
            )
            return ActionIntent(ActionType.MOVE, tx, ty, decision=decision)

    if can_mine(agent, world) and inventory_ratio < 0.9:
        decision = DecisionRecord(
            agent_id=agent.id,
            tick=tick,
            observed_inputs=inputs,
            selected_action=ActionType.MINE.value,
            competing_actions=["move"],
            policy_scores={"mine": 0.85},
            current_goal="extract_resources",
            interpretation="On mineable cell with inventory space",
        )
        return ActionIntent(ActionType.MINE, decision=decision)

    if inventory_ratio < 0.8 and agent.hardware.mining_ability > 0.2:
        resource_pos = _find_nearest_resource_to_mine(agent, world)
        if resource_pos:
            tx, ty = _step_toward(agent, resource_pos[0], resource_pos[1])
            decision = DecisionRecord(
                agent_id=agent.id,
                tick=tick,
                observed_inputs=inputs,
                selected_action=ActionType.MOVE.value,
                competing_actions=["explore"],
                policy_scores={"seek_resource": 0.7, "explore": 0.3},
                current_goal="seek_resources",
                interpretation="Inventory has space, moving toward resources",
            )
            return ActionIntent(ActionType.MOVE, tx, ty, decision=decision)

    if energy_ratio < 0.5:
        source = _find_nearest_terrain(agent, world, {TerrainType.ENERGY_SOURCE, TerrainType.CHARGING_STATION})
        if source:
            tx, ty = _step_toward(agent, source[0], source[1])
            decision = DecisionRecord(
                agent_id=agent.id,
                tick=tick,
                observed_inputs=inputs,
                selected_action=ActionType.MOVE.value,
                competing_actions=["mine", "explore"],
                policy_scores={"seek_energy": 0.75},
                current_goal="seek_energy",
                interpretation=f"Energy at {energy_ratio:.0%}, heading to power source",
            )
            return ActionIntent(ActionType.MOVE, tx, ty, decision=decision)

    tx, ty = _explore_direction(agent, world, rng)
    decision = DecisionRecord(
        agent_id=agent.id,
        tick=tick,
        observed_inputs=inputs,
        selected_action=ActionType.MOVE.value,
        competing_actions=["idle"],
        policy_scores={"explore": 0.6, "idle": 0.1},
        relevant_memory={"visit_count": len(agent.visit_map)},
        current_goal="explore",
        interpretation="No urgent needs, exploring least-visited area",
    )
    return ActionIntent(ActionType.MOVE, tx, ty, decision=decision)
