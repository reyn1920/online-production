# TRAE.AI Agentic Framework Module
# 
# This module contains the core agentic framework for TRAE.AI system.
# It provides base classes and specialized agents for autonomous task execution.
#
# Author: TRAE.AI System
# Version: 1.0.0

from .base_agents import PlannerAgent, ExecutorAgent, AuditorAgent
from .specialized_agents import (
    SystemAgent,
    ResearchAgent,
    ContentAgent,
    MarketingAgent,
    QAAgent
)

__all__ = [
    'PlannerAgent',
    'ExecutorAgent', 
    'AuditorAgent',
    'SystemAgent',
    'ResearchAgent',
    'ContentAgent',
    'MarketingAgent',
    'QAAgent'
]

__version__ = '1.0.0'
__author__ = 'TRAE.AI System'