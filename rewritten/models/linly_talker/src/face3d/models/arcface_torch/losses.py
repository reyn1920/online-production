"""Loss functions for face recognition models.

This module provides CosFace and ArcFace loss implementations.
Requires PyTorch to be installed for actual usage.
"""

from __future__ import annotations
from typing import Any


def get_loss(name: str) -> CosFace | ArcFace:
    """Factory function to create loss functions.

    Args:
        name: Loss function name ('cosface' or 'arcface')

    Returns:
        Loss function instance

    Raises:
        ImportError: If PyTorch is not available
        ValueError: If loss name is unknown
    """
    # Check torch availability at runtime
    try:
        import torch  # noqa: F401
    except ImportError:
        raise ImportError(
            "PyTorch is required but not installed. Please install torch to use loss functions."
        )

    if name == "cosface":
        return CosFace()
    elif name == "arcface":
        return ArcFace()
    else:
        raise ValueError(f"Unknown loss function: {name}")


class CosFace:
    """CosFace loss implementation.

    Args:
        s: Scale parameter (default: 64.0)
        m: Margin parameter (default: 0.40)
    """

    def __init__(self, s: float = 64.0, m: float = 0.40) -> None:
        self.s = s
        self.m = m

    def forward(self, cosine: Any, label: Any) -> Any:
        """Forward pass for CosFace loss.

        Args:
            cosine: Cosine similarity tensor
            label: Ground truth labels

        Returns:
            Loss tensor

        Raises:
            ImportError: If PyTorch is not available
        """
        try:
            import torch
        except ImportError:
            raise ImportError("PyTorch is required for forward pass")

        index = torch.where(label != -1)[0]
        m_hot = torch.zeros(index.size()[0], cosine.size()[1], device=cosine.device)
        m_hot.scatter_(1, label[index, None], self.m)
        cosine[index] -= m_hot
        ret = cosine * self.s
        return ret


class ArcFace:
    """ArcFace loss implementation.

    Args:
        s: Scale parameter (default: 64.0)
        m: Margin parameter (default: 0.05)
    """

    def __init__(self, s: float = 64.0, m: float = 0.05) -> None:
        self.s = s
        self.m = m

    def forward(self, cosine: Any, label: Any) -> Any:
        """Forward pass for ArcFace loss.

        Args:
            cosine: Cosine similarity tensor
            label: Ground truth labels

        Returns:
            Loss tensor

        Raises:
            ImportError: If PyTorch is not available
        """
        try:
            import torch
        except ImportError:
            raise ImportError("PyTorch is required for forward pass")

        index = torch.where(label != -1)[0]
        m_hot = torch.zeros(index.size()[0], cosine.size()[1], device=cosine.device)
        m_hot.scatter_(1, label[index, None], self.m)
        cosine.acos_()
        cosine[index] += m_hot
        cosine.cos_().mul_(self.s)
        return cosine
