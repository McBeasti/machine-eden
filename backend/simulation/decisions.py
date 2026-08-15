"""Decision transparency records."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DecisionRecord:
    """Compact explanation of why an agent acted."""

    agent_id: str
    tick: int
    observed_inputs: dict[str, Any]
    selected_action: str
    competing_actions: list[str] = field(default_factory=list)
    policy_scores: dict[str, float] = field(default_factory=dict)
    relevant_memory: dict[str, Any] = field(default_factory=dict)
    expected_reward: float | None = None
    current_goal: str = ""
    hardware_constraints: list[str] = field(default_factory=list)
    interpretation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "tick": self.tick,
            "observed_inputs": self.observed_inputs,
            "selected_action": self.selected_action,
            "competing_actions": self.competing_actions,
            "policy_scores": self.policy_scores,
            "relevant_memory": self.relevant_memory,
            "expected_reward": self.expected_reward,
            "current_goal": self.current_goal,
            "hardware_constraints": self.hardware_constraints,
            "interpretation": self.interpretation,
            "source": "rule_based",
        }


class DecisionLog:
    """Stores recent decisions per agent."""

    def __init__(self, max_per_agent: int = 10) -> None:
        self._decisions: dict[str, list[DecisionRecord]] = {}
        self.max_per_agent = max_per_agent

    def record(self, decision: DecisionRecord) -> None:
        aid = decision.agent_id
        if aid not in self._decisions:
            self._decisions[aid] = []
        self._decisions[aid].append(decision)
        if len(self._decisions[aid]) > self.max_per_agent:
            self._decisions[aid] = self._decisions[aid][-self.max_per_agent :]

    def get_agent(self, agent_id: str) -> list[dict]:
        return [d.to_dict() for d in self._decisions.get(agent_id, [])]

    def clear(self) -> None:
        self._decisions.clear()
