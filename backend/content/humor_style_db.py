#!/usr/bin/env python3
"""
Humor Style Database for The Right Perspective Channel

This module provides humor and style generation specifically for "The Right Perspective" channel.
It's part of the Protected Channel Protocol and should maintain the channel's unique
witty/sarcastic tone for political commentary.

PROTECTED CHANNEL COMPONENT - DO NOT MODIFY
"""

import logging
import random
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import sqlite3
import json

logger = logging.getLogger(__name__)

@dataclass
class HumorStyle:
    """Represents a humor style configuration for The Right Perspective."""
    style_name: str
    tone_descriptors: List[str]
    opening_phrases: List[str]
    transition_phrases: List[str]
    closing_phrases: List[str]
    sarcasm_level: float  # 0.0 to 1.0
    wit_intensity: float  # 0.0 to 1.0

class HumorStyleDatabase:
    """
    Database manager for The Right Perspective's humor and style generation.
    
    This class is part of the Protected Channel Protocol and provides the unique
    witty/sarcastic "banter" that defines The Right Perspective's content style.
    """
    
    def __init__(self, db_path: str = "./data/right_perspective.db"):
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(__name__)
        
        # Protected Channel validation
        self._validate_protected_channel()
        
        # Initialize humor styles for The Right Perspective
        self.humor_styles = self._load_humor_styles()
        
        self.logger.info("Humor Style Database initialized for The Right Perspective (PROTECTED)")
    
    def _validate_protected_channel(self) -> None:
        """Validate that this is being used for The Right Perspective channel only."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM channels WHERE channel_name = 'The Right Perspective'"
                )
                if cursor.fetchone()[0] == 0:
                    raise ValueError("PROTECTED CHANNEL ERROR: The Right Perspective channel not found in database")
        except Exception as e:
            self.logger.error(f"Protected channel validation failed: {e}")
            raise
    
    def _load_humor_styles(self) -> Dict[str, HumorStyle]:
        """Load The Right Perspective's signature humor styles."""
        return {
            "political_hypocrisy": HumorStyle(
                style_name="Political Hypocrisy Exposé",
                tone_descriptors=["sarcastic", "incisive", "fact-based", "witty"],
                opening_phrases=[
                    "Well, well, well... look what we have here.",
                    "You know what's fascinating about politicians?",
                    "Let me get this straight...",
                    "Oh, this is rich.",
                    "I love it when politicians think we have amnesia.",
                    "Here's a fun little contradiction for you."
                ],
                transition_phrases=[
                    "But wait, there's more!",
                    "Plot twist:",
                    "Here's where it gets interesting...",
                    "Now, let's rewind to...",
                    "Fast forward to today, and...",
                    "The receipts don't lie, folks."
                ],
                closing_phrases=[
                    "The hypocrisy is almost impressive.",
                    "You can't make this stuff up.",
                    "And that, folks, is how you spot a flip-flopper.",
                    "The receipts speak for themselves.",
                    "Remember this the next time they try to gaslight you.",
                    "Politics: where consistency goes to die."
                ],
                sarcasm_level=0.8,
                wit_intensity=0.9
            ),
            "breaking_news_analysis": HumorStyle(
                style_name="Breaking News Reality Check",
                tone_descriptors=["analytical", "skeptical", "humorous", "direct"],
                opening_phrases=[
                    "Breaking news just broke, and so did my faith in journalism.",
                    "Let's unpack this latest political theater, shall we?",
                    "The news cycle is spinning faster than a politician's excuses.",
                    "Time for a reality check on today's headlines.",
                    "Another day, another political plot twist."
                ],
                transition_phrases=[
                    "Meanwhile, in reality...",
                    "The plot thickens...",
                    "But here's what they're not telling you:",
                    "Let's connect the dots, shall we?",
                    "The timing is... interesting."
                ],
                closing_phrases=[
                    "Stay skeptical, stay informed.",
                    "Question everything, especially the convenient narratives.",
                    "The truth is usually somewhere between the headlines.",
                    "Keep your critical thinking caps on, folks.",
                    "Remember: if it sounds too convenient, it probably is."
                ],
                sarcasm_level=0.6,
                wit_intensity=0.7
            ),
            "evidence_presentation": HumorStyle(
                style_name="Evidence-Based Roasting",
                tone_descriptors=["methodical", "devastating", "fact-driven", "entertaining"],
                opening_phrases=[
                    "Time to present the evidence, your honor.",
                    "Let's go to the receipts, shall we?",
                    "The facts are about to get uncomfortable.",
                    "Evidence time! *cracks knuckles*",
                    "Buckle up, we're going fact-checking."
                ],
                transition_phrases=[
                    "Exhibit A:",
                    "But wait, there's documentation!",
                    "The paper trail tells a different story...",
                    "According to their own words...",
                    "The evidence suggests otherwise..."
                ],
                closing_phrases=[
                    "Case closed.",
                    "The evidence has spoken.",
                    "Facts don't care about your narrative.",
                    "And that's how you fact-check with style.",
                    "Truth: 1, Spin: 0."
                ],
                sarcasm_level=0.7,
                wit_intensity=0.8
            )
        }
    
    def generate_humor_content(self, 
                             topic: str, 
                             evidence_data: Dict[str, Any], 
                             style_preference: str = "political_hypocrisy") -> Dict[str, Any]:
        """
        Generate humorous content for The Right Perspective based on evidence data.
        
        Args:
            topic: The topic/subject being covered
            evidence_data: Data from the evidence table
            style_preference: Which humor style to use
            
        Returns:
            Dictionary containing generated humor content
        """
        try:
            if style_preference not in self.humor_styles:
                style_preference = "political_hypocrisy"  # Default fallback
            
            style = self.humor_styles[style_preference]
            
            # Generate content structure
            content = {
                "opening": random.choice(style.opening_phrases),
                "transition": random.choice(style.transition_phrases),
                "closing": random.choice(style.closing_phrases),
                "tone_guidance": {
                    "descriptors": style.tone_descriptors,
                    "sarcasm_level": style.sarcasm_level,
                    "wit_intensity": style.wit_intensity
                },
                "content_hooks": self._generate_content_hooks(topic, evidence_data),
                "fact_integration_phrases": self._get_fact_integration_phrases(),
                "style_name": style.style_name
            }
            
            self.logger.info(f"Generated humor content for topic: {topic} using style: {style_preference}")
            return content
            
        except Exception as e:
            self.logger.error(f"Error generating humor content: {e}")
            return self._get_fallback_content()
    
    def _generate_content_hooks(self, topic: str, evidence_data: Dict[str, Any]) -> List[str]:
        """Generate topic-specific content hooks based on evidence."""
        hooks = [
            f"Let's talk about {topic} and the fascinating world of political memory loss.",
            f"Today's episode of 'Things Politicians Hope You'll Forget' features {topic}.",
            f"The {topic} situation is a masterclass in political gymnastics.",
            f"Breaking: Local politician discovers {topic}, immediately forgets previous position.",
            f"In today's edition of 'Receipts vs. Reality,' we examine {topic}."
        ]
        
        # Add evidence-specific hooks if available
        if evidence_data.get('content_type') == 'quote':
            hooks.append(f"Someone said something about {topic}. Plot twist: they said the opposite before.")
        elif evidence_data.get('content_type') == 'statistic':
            hooks.append(f"The numbers on {topic} are in, and they're not what politicians claimed.")
        
        return hooks
    
    def _get_fact_integration_phrases(self) -> List[str]:
        """Get phrases for smoothly integrating facts into humorous content."""
        return [
            "According to the receipts...",
            "The documentation shows...",
            "Here's what actually happened...",
            "The timeline reveals...",
            "Public records indicate...",
            "Their own words prove...",
            "The evidence suggests...",
            "Historical data confirms...",
            "The facts paint a different picture...",
            "Reality check: the data shows..."
        ]
    
    def _get_fallback_content(self) -> Dict[str, Any]:
        """Provide fallback content if generation fails."""
        return {
            "opening": "Well, this is awkward...",
            "transition": "But here's the thing...",
            "closing": "The truth has a way of surfacing.",
            "tone_guidance": {
                "descriptors": ["witty", "factual", "engaging"],
                "sarcasm_level": 0.5,
                "wit_intensity": 0.6
            },
            "content_hooks": ["Let's dive into today's political reality check."],
            "fact_integration_phrases": ["The facts show..."],
            "style_name": "Default Fallback"
        }
    
    def get_available_styles(self) -> List[str]:
        """Get list of available humor styles."""
        return list(self.humor_styles.keys())
    
    def get_style_details(self, style_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific humor style."""
        if style_name in self.humor_styles:
            style = self.humor_styles[style_name]
            return {
                "name": style.style_name,
                "tone_descriptors": style.tone_descriptors,
                "sarcasm_level": style.sarcasm_level,
                "wit_intensity": style.wit_intensity,
                "sample_opening": style.opening_phrases[0],
                "sample_closing": style.closing_phrases[0]
            }
        return None
    
    def validate_protected_status(self) -> bool:
        """
        Validate that The Right Perspective channel maintains its protected status.
        
        Returns:
            True if channel is properly protected, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check channel protection
                cursor.execute(
                    "SELECT notes FROM channels WHERE channel_name = 'The Right Perspective'"
                )
                result = cursor.fetchone()
                
                if not result or "PROTECTED CHANNEL" not in result[0]:
                    self.logger.error("PROTECTION BREACH: The Right Perspective channel protection compromised")
                    return False
                
                # Check persona protection
                cursor.execute(
                    "SELECT writing_style_description FROM author_personas WHERE channel_name = 'The Right Perspective'"
                )
                result = cursor.fetchone()
                
                if not result or "PROTECTED READ-ONLY PERSONA" not in result[0]:
                    self.logger.error("PROTECTION BREACH: The Right Perspective persona protection compromised")
                    return False
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error validating protected status: {e}")
            return False

# Protected Channel Protocol Enforcement
def get_humor_style_for_right_perspective(topic: str, evidence_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for The Right Perspective humor style generation.
    This function enforces the Protected Channel Protocol.
    """
    humor_db = HumorStyleDatabase()
    
    # Validate protection before proceeding
    if not humor_db.validate_protected_status():
        raise RuntimeError("PROTECTED CHANNEL VIOLATION: The Right Perspective protection compromised")
    
    return humor_db.generate_humor_content(topic, evidence_data)

if __name__ == "__main__":
    # Test the humor style database
    humor_db = HumorStyleDatabase()
    
    # Test content generation
    test_evidence = {
        "topic": "Healthcare Policy",
        "content": "Politicians flip-flopping on healthcare",
        "content_type": "quote"
    }
    
    result = humor_db.generate_humor_content("Healthcare Policy", test_evidence)
    print(json.dumps(result, indent=2))