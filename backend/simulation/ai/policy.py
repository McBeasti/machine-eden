"""PyTorch policy network placeholder for Phase 2."""

from __future__ import annotations

try:
    import torch
    import torch.nn as nn
except ImportError:  # pragma: no cover - optional ML dependency
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]


if nn is not None:

    class PolicyNetwork(nn.Module):
        """Compact feedforward policy for neuroevolution (Phase 2)."""

        INPUT_SIZE = 16
        OUTPUT_SIZE = 8

        def __init__(self) -> None:
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(self.INPUT_SIZE, 32),
                nn.ReLU(),
                nn.Linear(32, 16),
                nn.ReLU(),
                nn.Linear(16, self.OUTPUT_SIZE),
                nn.Tanh(),
            )

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return self.net(x)

        @classmethod
        def random(cls, seed: int | None = None) -> "PolicyNetwork":
            if seed is not None:
                torch.manual_seed(seed)
            net = cls()
            for p in net.parameters():
                nn.init.uniform_(p, -0.5, 0.5)
            return net

else:

    class PolicyNetwork:  # type: ignore[no-redef]
        """Stub when torch is not installed."""

        INPUT_SIZE = 16
        OUTPUT_SIZE = 8

        def __init__(self) -> None:
            raise ImportError("Install torch via requirements-ml.txt to use PolicyNetwork")

        @classmethod
        def random(cls, seed: int | None = None) -> "PolicyNetwork":
            raise ImportError("Install torch via requirements-ml.txt to use PolicyNetwork")
