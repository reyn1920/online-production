# TRAE.AI Agentic Framework Module
#
# This module contains the core agentic framework for TRAE.AI system.
# It provides base classes and specialized agents for autonomous task execution.
#
# Author: TRAE.AI System
# Version: 1.0.0

from .base_agents import AuditorAgent, ExecutorAgent, PlannerAgent
from .specialized_agents import (
    ContentAgent,
    MarketingAgent,
    QAAgent,
    ResearchAgent,
    SystemAgent,
# BRACKET_SURGEON: disabled
# )

__all__ = [
    "PlannerAgent",
    "ExecutorAgent",
    "AuditorAgent",
    "SystemAgent",
    "ResearchAgent",
    "ContentAgent",
    "MarketingAgent",
    "QAAgent",
# BRACKET_SURGEON: disabled
# ]

__version__ = "1.0.0"
__author__ = "TRAE.AI System"