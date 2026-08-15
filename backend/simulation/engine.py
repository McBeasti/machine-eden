"""Main simulation engine and tick loop."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from simulation.actions import (
    ENERGY_COSTS,
    HARVEST_RATE,
    RECHARGE_RATE,
    ActionType,
    can_harvest,
    can_mine,
    can_recharge,
    mine_yield,
    move_cost,
)
from simulation.agent import Agent, create_agent
from simulation.ai.rules import decide
from simulation.config import SimulationConfig
from simulation.decisions import DecisionLog
from simulation.events import EventLog, SimulationEvent
from simulation.metrics import MetricsCollector
from simulation.spatial import SpatialIndex
from simulation.world import TERRAIN_NAMES, TerrainType, World


class SimulationEngine:
    """Owns world state, agents, and the tick loop."""

    def __init__(self, config: SimulationConfig | None = None) -> None:
        self.config = config or SimulationConfig()
        self.rng = np.random.default_rng(self.config.seed)
        self.tick = 0
        self.running = False
        self.speed_multiplier = 1.0

        self.world: World | None = None
        self.agents: dict[str, Agent] = {}
        self.spatial = SpatialIndex(cell_size=8)
        self.events = EventLog()
        self.decisions = DecisionLog()
        self.metrics = MetricsCollector()

        self._reset_internal()

    def _reset_internal(self) -> None:
        """Initialize world and agents from current config and seed."""
        self.rng = np.random.default_rng(self.config.seed)
        self.tick = 0
        self.world = World(self.config, self.rng)
        self.agents.clear()
        self.spatial.clear()
        self.events.clear()
        self.decisions.clear()
        self.metrics.clear()

        assert self.world is not None
        w, h = self.world.width, self.world.height
        for _ in range(self.config.initial_population):
            x = int(self.rng.integers(0, w))
            y = int(self.rng.integers(0, h))
            agent = create_agent(self.rng, x, y, tick=0)
            agent.hardware.energy_consumption *= self.config.energy_scarcity
            self.agents[agent.id] = agent
            self.spatial.insert(agent.id, x, y)
            self.events.emit(
                SimulationEvent(
                    tick=0,
                    event_type="spawn",
                    actor_id=agent.id,
                    location=(x, y),
                    actors=[agent.id],
                    lineage_id=agent.lineage_id,
                )
            )
            self.metrics.record_birth()

    def reset(self, config: SimulationConfig | None = None) -> None:
        if config:
            self.config = config
        self._reset_internal()

    def step(self) -> dict[str, Any]:
        """Advance simulation by one tick. Returns state delta."""
        if self.world is None:
            raise RuntimeError("Simulation not initialized")

        self.tick += 1
        self.metrics.reset_tick_counters()
        deaths_this_tick = 0
        cfg = self.config
        scarcity = cfg.energy_scarcity

        for agent_id in sorted(self.agents.keys()):
            agent = self.agents[agent_id]
            if not agent.alive:
                continue

            agent.age += 1
            intent = decide(agent, self.world, cfg, self.tick, self.rng)
            if intent.decision:
                self.decisions.record(intent.decision)

            agent.set_intent(intent.action.value, intent.target_x, intent.target_y)
            self._execute_action(agent, intent, scarcity)

            idle_cost = ENERGY_COSTS[ActionType.IDLE] * agent.hardware.energy_consumption * scarcity
            agent.spend_energy(idle_cost)
            self.metrics.record_energy_consumed(idle_cost)

            hazard = float(self.world.hazard_level[agent.y, agent.x])
            if hazard > 0:
                dmg = hazard * cfg.environmental_danger * 0.5
                agent.damage += dmg
                agent.spend_energy(dmg * 0.5)

            agent.visit_map[(agent.x, agent.y)] = agent.visit_map.get((agent.x, agent.y), 0) + 1
            agent.clamp_energy()

            if agent.energy <= 0:
                agent.alive = False
                agent.current_task = "dead"
                deaths_this_tick += 1
                self.metrics.record_death(agent.age)
                self._handle_death(agent)

        regen_events = self.world.regenerate(self.rng)
        for x, y, amount in regen_events:
            self.events.emit(
                SimulationEvent(
                    tick=self.tick,
                    event_type="regenerate",
                    location=(x, y),
                    resources={"amount": amount},
                    metadata={"terrain": TERRAIN_NAMES[int(self.world.terrain[y, x])]},
                )
            )

        self.spatial.rebuild(self.agents)
        m = self.metrics.compute(
            self.tick,
            self.agents,
            self.world.resources,
            births_this_tick=0,
            deaths_this_tick=deaths_this_tick,
        )

        return self._build_delta(m)

    def _execute_action(self, agent: Agent, intent, scarcity: float) -> None:
        assert self.world is not None
        action = intent.action
        agent.current_task = action.value

        if action == ActionType.MOVE:
            tx = intent.target_x if intent.target_x is not None else agent.x
            ty = intent.target_y if intent.target_y is not None else agent.y
            if not self.world.in_bounds(tx, ty):
                return
            if tx == agent.x and ty == agent.y:
                return
            mc = float(self.world.movement_cost[ty, tx])
            dist = math.sqrt((tx - agent.x) ** 2 + (ty - agent.y) ** 2)
            cost = move_cost(dist, mc, scarcity)
            if not agent.spend_energy(cost):
                return
            self.metrics.record_energy_consumed(cost)
            old = (agent.x, agent.y)
            agent.x, agent.y = tx, ty
            self.spatial.update(agent.id, tx, ty)
            self.events.emit(
                SimulationEvent(
                    tick=self.tick,
                    event_type="move",
                    actor_id=agent.id,
                    location=(tx, ty),
                    actors=[agent.id],
                    metadata={"from": list(old)},
                )
            )

        elif action == ActionType.MINE:
            if not can_mine(agent, self.world):
                return
            cost = ENERGY_COSTS[ActionType.MINE] * scarcity
            if not agent.spend_energy(cost):
                return
            self.metrics.record_energy_consumed(cost)
            terrain = self.world.get_terrain(agent.x, agent.y)
            resource_name = TERRAIN_NAMES[terrain.value]
            yield_amt = mine_yield(agent, self.world)
            self.world.resources[agent.y, agent.x] -= yield_amt
            added = agent.add_to_inventory(resource_name, yield_amt)
            self.metrics.record_mining(added)
            self.events.emit(
                SimulationEvent(
                    tick=self.tick,
                    event_type="mine",
                    actor_id=agent.id,
                    location=(agent.x, agent.y),
                    resources={resource_name: added},
                    outcome="success" if added > 0 else "partial",
                )
            )

        elif action == ActionType.HARVEST:
            if not can_harvest(agent, self.world):
                return
            cost = ENERGY_COSTS[ActionType.HARVEST] * scarcity
            if not agent.spend_energy(cost):
                return
            self.metrics.record_energy_consumed(cost)
            harvested = HARVEST_RATE * (1.0 + agent.hardware.mining_ability * 0.2)
            cap = agent.hardware.energy_capacity - agent.energy
            gained = min(harvested, cap)
            agent.energy += gained
            agent.clamp_energy()
            self.metrics.record_energy_produced(gained)
            self.events.emit(
                SimulationEvent(
                    tick=self.tick,
                    event_type="harvest",
                    actor_id=agent.id,
                    location=(agent.x, agent.y),
                    resources={"energy": gained},
                )
            )

        elif action == ActionType.RECHARGE:
            if not can_recharge(agent, self.world):
                return
            cost = ENERGY_COSTS[ActionType.RECHARGE] * scarcity
            if not agent.spend_energy(cost):
                return
            self.metrics.record_energy_consumed(cost)
            cap = agent.hardware.energy_capacity - agent.energy
            gained = min(RECHARGE_RATE, cap)
            agent.energy += gained
            agent.clamp_energy()
            self.metrics.record_energy_produced(gained)
            self.events.emit(
                SimulationEvent(
                    tick=self.tick,
                    event_type="recharge",
                    actor_id=agent.id,
                    location=(agent.x, agent.y),
                    resources={"energy": gained},
                )
            )

        elif action == ActionType.IDLE:
            agent.current_task = "idle"

    def _handle_death(self, agent: Agent) -> None:
        assert self.world is not None
        if agent.inventory:
            for rtype, amount in agent.inventory.items():
                self.world.resources[agent.y, agent.x] += amount * 0.5
            self.events.emit(
                SimulationEvent(
                    tick=self.tick,
                    event_type="drop",
                    actor_id=agent.id,
                    location=(agent.x, agent.y),
                    resources=dict(agent.inventory),
                )
            )
            agent.inventory.clear()

        self.spatial.remove(agent.id)
        self.events.emit(
            SimulationEvent(
                tick=self.tick,
                event_type="death",
                actor_id=agent.id,
                location=(agent.x, agent.y),
                actors=[agent.id],
                lineage_id=agent.lineage_id,
                outcome="energy_depletion",
                metadata={"age": agent.age},
            )
        )

    def _build_delta(self, metrics) -> dict[str, Any]:
        alive_agents = [a.to_dict() for a in self.agents.values() if a.alive]
        return {
            "tick": self.tick,
            "population": len(alive_agents),
            "agents": alive_agents,
            "metrics": metrics.to_dict(),
            "events": self.events.recent(50),
        }

    def get_state(self) -> dict[str, Any]:
        """Full state snapshot for initial load."""
        assert self.world is not None
        return {
            "tick": self.tick,
            "running": self.running,
            "speed": self.speed_multiplier,
            "config": self.config.model_dump(),
            "world": self.world.to_dict(),
            "agents": [a.to_dict() for a in self.agents.values() if a.alive],
            "metrics": self.metrics.get_history(200),
            "events": self.events.recent(100),
        }

    def get_agent(self, agent_id: str) -> dict[str, Any] | None:
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        return {
            **agent.to_dict(),
            "decisions": self.decisions.get_agent(agent_id),
            "alive": agent.alive,
        }
