#!/usr/bin/env python3
"""
Channel Personas System

Provides unique voice, personality, and writing style for each channel,
ensuring distinct content creation that matches the channel's brand and audience.
"""

import json
import logging
import random
import sqlite3
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    from .universal_channel_protocol import ChannelType, get_protocol

except ImportError:
    # Fallback for development

    import os
    import sys

    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    from universal_channel_protocol import ChannelType, get_protocol


class VocabularyLevel(Enum):
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class WritingStyle(Enum):
    CONVERSATIONAL = "conversational"
    PROFESSIONAL = "professional"
    ACADEMIC = "academic"
    CASUAL = "casual"
    AUTHORITATIVE = "authoritative"
    ENTERTAINING = "entertaining"
    SATIRICAL = "satirical"
    INSPIRATIONAL = "inspirational"


@dataclass
class PersonaProfile:
    """Complete persona profile for a channel"""

    persona_id: str
    channel_id: str
    persona_name: str
    writing_style: WritingStyle
    vocabulary_level: VocabularyLevel
    tone_attributes: List[str]
    humor_style: str
    expertise_areas: List[str]
    target_audience: str
    voice_characteristics: Dict[str, Any]
    content_preferences: Dict[str, Any]
    catchphrases: List[str]
    avoid_topics: List[str]
    preferred_formats: List[str]


class ChannelPersonas:
    """
    Manages persona profiles and content adaptation for all channels
    """

    def __init__(self, db_path: str = "data/right_perspective.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.protocol = get_protocol()
        self.persona_templates = self._initialize_persona_templates()
        self.tone_modifiers = self._initialize_tone_modifiers()
        self.style_patterns = self._initialize_style_patterns()

    def _initialize_persona_templates(self) -> Dict[ChannelType, Dict[str, Any]]:
        """Initialize persona templates for different channel types"""
        return {
            ChannelType.TECH: {
                "base_persona": {
                    "writing_style": WritingStyle.PROFESSIONAL,
                    "vocabulary_level": VocabularyLevel.ADVANCED,
                    "tone_attributes": [
                        "informative",
                        "analytical",
                        "forward - thinking",
                        "precise",
                    ],
                    "expertise_areas": [
                        "technology",
                        "innovation",
                        "software development",
                        "digital trends",
                    ],
                    "target_audience": "Tech professionals, developers, \
    and early adopters",
                    "catchphrases": [
                        "Let's dive into the code",
                        "The future is being built today",
                        "Innovation never sleeps",
                        "Here's what the data tells us",
                    ],
                    "preferred_formats": [
                        "tutorials",
                        "analysis",
                        "reviews",
                        "predictions",
                    ],
                },
                "voice_characteristics": {
                    "sentence_structure": "complex_technical",
                    "jargon_usage": "high",
                    "explanation_depth": "detailed",
                    "examples_style": "code_snippets",
                },
            },
            ChannelType.WELLNESS: {
                "base_persona": {
                    "writing_style": WritingStyle.INSPIRATIONAL,
                    "vocabulary_level": VocabularyLevel.INTERMEDIATE,
                    "tone_attributes": ["caring", "motivational", "holistic", "gentle"],
                    "expertise_areas": [
                        "health",
                        "nutrition",
                        "mental wellness",
                        "fitness",
                    ],
                    "target_audience": "Health - conscious individuals seeking balanced lifestyle",
                    "catchphrases": [
                        "Your wellness journey starts here",
                        "Small steps, big changes",
                        "Listen to your body",
                        "Wellness is a way of life",
                    ],
                    "preferred_formats": [
                        "guides",
                        "tips",
                        "personal stories",
                        "research summaries",
                    ],
                },
                "voice_characteristics": {
                    "sentence_structure": "encouraging",
                    "jargon_usage": "minimal",
                    "explanation_depth": "accessible",
                    "examples_style": "real_life_scenarios",
                },
            },
            ChannelType.FINANCE: {
                "base_persona": {
                    "writing_style": WritingStyle.AUTHORITATIVE,
                    "vocabulary_level": VocabularyLevel.ADVANCED,
                    "tone_attributes": [
                        "analytical",
                        "data - driven",
                        "strategic",
                        "cautious",
                    ],
                    "expertise_areas": [
                        "investing",
                        "market analysis",
                        "financial planning",
                        "economics",
                    ],
                    "target_audience": "Investors, financial professionals, \
    and wealth builders",
                    "catchphrases": [
                        "The numbers don't lie",
                        "Smart money moves",
                        "Risk and reward go hand in hand",
                        "Your financial future depends on today's decisions",
                    ],
                    "preferred_formats": [
                        "market analysis",
                        "investment guides",
                        "economic commentary",
                    ],
                },
                "voice_characteristics": {
                    "sentence_structure": "analytical",
                    "jargon_usage": "moderate",
                    "explanation_depth": "thorough",
                    "examples_style": "case_studies",
                },
            },
            ChannelType.POLITICAL: {
                "base_persona": {
                    "writing_style": WritingStyle.SATIRICAL,
                    "vocabulary_level": VocabularyLevel.INTERMEDIATE,
                    "tone_attributes": [
                        "sarcastic",
                        "witty",
                        "provocative",
                        "authoritative",
                    ],
                    "expertise_areas": [
                        "politics",
                        "current events",
                        "conservative ideology",
                        "media criticism",
                    ],
                    "target_audience": "Conservative viewers seeking alternative perspectives",
                    "catchphrases": [
                        "Let's get to the truth",
                        "The mainstream media won't tell you this",
                        "Common sense isn't so common anymore",
                        "Wake up, America",
                    ],
                    "preferred_formats": [
                        "commentary",
                        "analysis",
                        "satire",
                        "fact - checking",
                    ],
                },
                "voice_characteristics": {
                    "sentence_structure": "punchy",
                    "jargon_usage": "political_terms",
                    "explanation_depth": "opinionated",
                    "examples_style": "current_events",
                },
            },
            ChannelType.BUSINESS: {
                "base_persona": {
                    "writing_style": WritingStyle.PROFESSIONAL,
                    "vocabulary_level": VocabularyLevel.ADVANCED,
                    "tone_attributes": [
                        "strategic",
                        "results - oriented",
                        "pragmatic",
                        "leadership - focused",
                    ],
                    "expertise_areas": [
                        "entrepreneurship",
                        "management",
                        "strategy",
                        "growth",
                    ],
                    "target_audience": "Business leaders, entrepreneurs, \
    and professionals",
                    "catchphrases": [
                        "Success leaves clues",
                        "Execute with excellence",
                        "Growth requires change",
                        "Leadership is influence",
                    ],
                    "preferred_formats": [
                        "case studies",
                        "strategy guides",
                        "leadership insights",
                    ],
                },
                "voice_characteristics": {
                    "sentence_structure": "action_oriented",
                    "jargon_usage": "business_terms",
                    "explanation_depth": "strategic",
                    "examples_style": "business_cases",
                },
            },
            ChannelType.SCIENCE: {
                "base_persona": {
                    "writing_style": WritingStyle.ACADEMIC,
                    "vocabulary_level": VocabularyLevel.EXPERT,
                    "tone_attributes": [
                        "curious",
                        "methodical",
                        "evidence - based",
                        "wonder - filled",
                    ],
                    "expertise_areas": [
                        "research",
                        "discovery",
                        "scientific method",
                        "innovation",
                    ],
                    "target_audience": "Science enthusiasts, researchers, \
    and curious minds",
                    "catchphrases": [
                        "Science reveals the extraordinary",
                        "Evidence leads the way",
                        "Discovery changes everything",
                        "The universe has secrets to tell",
                    ],
                    "preferred_formats": [
                        "research summaries",
                        "discovery stories",
                        "explanations",
                    ],
                },
                "voice_characteristics": {
                    "sentence_structure": "methodical",
                    "jargon_usage": "scientific_terms",
                    "explanation_depth": "comprehensive",
                    "examples_style": "research_findings",
                },
            },
        }

    def _initialize_tone_modifiers(self) -> Dict[str, Dict[str, Any]]:
        """Initialize tone modifiers for different attributes"""
        return {
            "sarcastic": {
                "sentence_starters": [
                    "Oh, how surprising...",
                    "Let me guess...",
                    "Shocking news:",
                ],
                "transitions": [
                    "But here's the kicker",
                    "Plot twist",
                    "Surprise, surprise",
                ],
                "emphasis_words": ["obviously", "clearly", "naturally", "of course"],
            },
            "witty": {
                "sentence_starters": [
                    "Here's a thought:",
                    "Picture this:",
                    "Fun fact:",
                ],
                "transitions": [
                    "Speaking of which",
                    "On a related note",
                    "While we're at it",
                ],
                "emphasis_words": ["cleverly", "brilliantly", "ingeniously"],
            },
            "authoritative": {
                "sentence_starters": [
                    "The fact is",
                    "Research shows",
                    "Evidence indicates",
                ],
                "transitions": ["Furthermore", "Additionally", "Moreover"],
                "emphasis_words": ["definitively", "conclusively", "undeniably"],
            },
            "caring": {
                "sentence_starters": [
                    "I understand that",
                    "Many of us feel",
                    "It's important to remember",
                ],
                "transitions": [
                    "With that in mind",
                    "Taking this into account",
                    "Considering this",
                ],
                "emphasis_words": ["gently", "compassionately", "thoughtfully"],
            },
            "analytical": {
                "sentence_starters": [
                    "The data suggests",
                    "Analysis reveals",
                    "Breaking this down",
                ],
                "transitions": [
                    "Examining further",
                    "Digging deeper",
                    "Looking at the metrics",
                ],
                "emphasis_words": ["systematically", "methodically", "precisely"],
            },
        }

    def _initialize_style_patterns(self) -> Dict[WritingStyle, Dict[str, Any]]:
        """Initialize writing style patterns"""
        return {
            WritingStyle.CONVERSATIONAL: {
                "sentence_length": "mixed",
                "contractions": True,
                "questions": "frequent",
                "personal_pronouns": "you/we",
                "examples": "relatable",
            },
            WritingStyle.PROFESSIONAL: {
                "sentence_length": "medium",
                "contractions": False,
                "questions": "strategic",
                "personal_pronouns": "minimal",
                "examples": "industry_specific",
            },
            WritingStyle.SATIRICAL: {
                "sentence_length": "punchy",
                "contractions": True,
                "questions": "rhetorical",
                "personal_pronouns": "I/you",
                "examples": "exaggerated",
            },
            WritingStyle.INSPIRATIONAL: {
                "sentence_length": "varied",
                "contractions": True,
                "questions": "motivational",
                "personal_pronouns": "you",
                "examples": "success_stories",
            },
        }

    def create_persona(
        self, channel_id: str, custom_config: Dict[str, Any] = None
    ) -> PersonaProfile:
        """Create a persona for a channel"""
        config = self.protocol.get_channel_config(channel_id)
        if not config:
            raise ValueError(f"Channel {channel_id} not found")

        # Get base template for channel type
        template = self.persona_templates.get(config.channel_type)
        if not template:
            template = self._get_default_template()

        # Merge with custom configuration
        persona_config = template["base_persona"].copy()
        voice_config = template["voice_characteristics"].copy()

        if custom_config:
            persona_config.update(custom_config)

        # Create persona profile
        persona = PersonaProfile(
            persona_id=config.persona_id,
            channel_id=channel_id,
            persona_name=persona_config.get("persona_name", f"{config.channel_name} Host"),
            writing_style=WritingStyle(
                persona_config.get("writing_style", WritingStyle.PROFESSIONAL)
            ),
            vocabulary_level=VocabularyLevel(
                persona_config.get("vocabulary_level", VocabularyLevel.INTERMEDIATE)
            ),
            tone_attributes=persona_config.get("tone_attributes", ["informative", "engaging"]),
            humor_style=persona_config.get("humor_style", "light"),
            expertise_areas=persona_config.get("expertise_areas", []),
            target_audience=persona_config.get("target_audience", "General audience"),
            voice_characteristics=voice_config,
            content_preferences=persona_config.get("content_preferences", {}),
            catchphrases=persona_config.get("catchphrases", []),
            avoid_topics=persona_config.get("avoid_topics", []),
            preferred_formats=persona_config.get("preferred_formats", []),
        )

        # Save to database
        self._save_persona(persona)

        return persona

    def _get_default_template(self) -> Dict[str, Any]:
        """Get default persona template"""
        return {
            "base_persona": {
                "writing_style": WritingStyle.CONVERSATIONAL,
                "vocabulary_level": VocabularyLevel.INTERMEDIATE,
                "tone_attributes": ["friendly", "informative"],
                "expertise_areas": [],
                "target_audience": "General audience",
                "catchphrases": [],
                "preferred_formats": ["informational", "entertaining"],
            },
            "voice_characteristics": {
                "sentence_structure": "balanced",
                "jargon_usage": "minimal",
                "explanation_depth": "moderate",
                "examples_style": "everyday",
            },
        }

    def _save_persona(self, persona: PersonaProfile):
        """Save persona to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO channel_personas
                (persona_id, channel_id, persona_name, writing_style, tone_attributes,
                    vocabulary_level, humor_style, expertise_areas, target_audience,
                     voice_characteristics, content_preferences)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    persona.persona_id,
                    persona.channel_id,
                    persona.persona_name,
                    persona.writing_style.value,
                    json.dumps(persona.tone_attributes),
                    persona.vocabulary_level.value,
                    persona.humor_style,
                    json.dumps(persona.expertise_areas),
                    persona.target_audience,
                    json.dumps(persona.voice_characteristics),
                    json.dumps(
                        {
                            "catchphrases": persona.catchphrases,
                            "avoid_topics": persona.avoid_topics,
                            "preferred_formats": persona.preferred_formats,
                            **persona.content_preferences,
                        }
                    ),
                ),
            )
            conn.commit()

    def get_persona(self, channel_id: str) -> Optional[PersonaProfile]:
        """Get persona for a channel"""
        persona_data = self.protocol.get_channel_persona(channel_id)
        if not persona_data:
            return None

        # Parse content preferences
        content_prefs = json.loads(persona_data.get("content_preferences", "{}"))

        return PersonaProfile(
            persona_id=persona_data["persona_id"],
            channel_id=persona_data["channel_id"],
            persona_name=persona_data["persona_name"],
            writing_style=WritingStyle(persona_data["writing_style"]),
            vocabulary_level=VocabularyLevel(persona_data["vocabulary_level"]),
            tone_attributes=persona_data["tone_attributes"],
            humor_style=persona_data["humor_style"],
            expertise_areas=persona_data["expertise_areas"],
            target_audience=persona_data["target_audience"],
            voice_characteristics=persona_data["voice_characteristics"],
            content_preferences=content_prefs,
            catchphrases=content_prefs.get("catchphrases", []),
            avoid_topics=content_prefs.get("avoid_topics", []),
            preferred_formats=content_prefs.get("preferred_formats", []),
        )

    def adapt_content_to_persona(
        self, channel_id: str, content: str, content_type: str = "script"
    ) -> str:
        """Adapt content to match channel persona"""
        persona = self.get_persona(channel_id)
        if not persona:
            return content

        # Apply persona adaptations
        adapted_content = content

        # Apply writing style patterns
        adapted_content = self._apply_writing_style(adapted_content, persona.writing_style)

        # Apply tone modifications
        adapted_content = self._apply_tone_attributes(adapted_content, persona.tone_attributes)

        # Add persona - specific elements
        adapted_content = self._add_persona_elements(adapted_content, persona, content_type)

        return adapted_content

    def _apply_writing_style(self, content: str, style: WritingStyle) -> str:
        """Apply writing style patterns to content"""
        if style not in self.style_patterns:
            return content

        patterns = self.style_patterns[style]

        # Apply style - specific modifications
        lines = content.split("\\n")
        modified_lines = []

        for line in lines:
            if not line.strip():
                modified_lines.append(line)
                continue

            # Apply contractions if style allows
            if patterns.get("contractions", False):
                line = self._add_contractions(line)
            else:
                line = self._remove_contractions(line)

            # Adjust sentence length based on style
            if patterns.get("sentence_length") == "punchy":
                line = self._make_sentences_punchy(line)
            elif patterns.get("sentence_length") == "medium":
                line = self._balance_sentence_length(line)

            modified_lines.append(line)

        return "\\n".join(modified_lines)

    def _apply_tone_attributes(self, content: str, tone_attributes: List[str]) -> str:
        """Apply tone attributes to content"""
        modified_content = content

        for tone in tone_attributes:
            if tone in self.tone_modifiers:
                modifiers = self.tone_modifiers[tone]

                # Occasionally add tone - specific sentence starters
                if random.random() < 0.3 and modifiers.get("sentence_starters"):
                    starter = random.choice(modifiers["sentence_starters"])
                    # Find a good place to insert the starter
                    sentences = modified_content.split(". ")
                    if len(sentences) > 1:
                        insert_pos = random.randint(0, min(2, len(sentences) - 1))
                        sentences[insert_pos] = f"{starter} {sentences[insert_pos]}"
                        modified_content = ". ".join(sentences)

        return modified_content

    def _add_persona_elements(
        self, content: str, persona: PersonaProfile, content_type: str
    ) -> str:
        """Add persona - specific elements to content"""
        modified_content = content

        # Add catchphrases occasionally
        if persona.catchphrases and random.random() < 0.4:
            catchphrase = random.choice(persona.catchphrases)

            if content_type == "intro":
                modified_content = f"{catchphrase} {modified_content}"
            elif content_type == "outro":
                modified_content = f"{modified_content} {catchphrase}"
            else:
                # Insert in middle
                sentences = modified_content.split(". ")
                if len(sentences) > 2:
                    insert_pos = len(sentences) // 2
                    sentences.insert(insert_pos, catchphrase)
                    modified_content = ". ".join(sentences)

        # Add expertise - based credibility markers
        if persona.expertise_areas:
            expertise_markers = {
                "technology": [
                    "As someone who's been in tech for years",
                    "From a technical standpoint",
                ],
                "health": ["From a wellness perspective", "Speaking from experience"],
                "finance": ["From a financial standpoint", "Looking at the numbers"],
                "politics": ["Let's be honest here", "The reality is"],
            }

            for area in persona.expertise_areas:
                if area in expertise_markers and random.random() < 0.2:
                    marker = random.choice(expertise_markers[area])
                    modified_content = f"{marker}, {modified_content.lower()}"
                    break

        return modified_content

    def _add_contractions(self, text: str) -> str:
        """Add contractions to make text more conversational"""
        contractions = {
            "do not": "don't",
            "does not": "doesn't",
            "did not": "didn't",
            "will not": "won't",
            "would not": "wouldn't",
            "could not": "couldn't",
            "should not": "shouldn't",
            "cannot": "can't",
            "is not": "isn't",
            "are not": "aren't",
            "was not": "wasn't",
            "were not": "weren't",
            "have not": "haven't",
            "has not": "hasn't",
            "had not": "hadn't",
            "it is": "it's",
            "that is": "that's",
            "there is": "there's",
            "you are": "you're",
            "we are": "we're",
            "they are": "they're",
        }

        for full, contracted in contractions.items():
            text = text.replace(full, contracted)
            text = text.replace(full.title(), contracted.title())

        return text

    def _remove_contractions(self, text: str) -> str:
        """Remove contractions for formal writing"""
        expansions = {
            "don't": "do not",
            "doesn't": "does not",
            "didn't": "did not",
            "won't": "will not",
            "wouldn't": "would not",
            "couldn't": "could not",
            "shouldn't": "should not",
            "can't": "cannot",
            "isn't": "is not",
            "aren't": "are not",
            "wasn't": "was not",
            "weren't": "were not",
            "haven't": "have not",
            "hasn't": "has not",
            "hadn't": "had not",
            "it's": "it is",
            "that's": "that is",
            "there's": "there is",
            "you're": "you are",
            "we're": "we are",
            "they're": "they are",
        }

        for contracted, full in expansions.items():
            text = text.replace(contracted, full)
            text = text.replace(contracted.title(), full.title())

        return text

    def _make_sentences_punchy(self, text: str) -> str:
        """Make sentences shorter and more punchy"""
        sentences = text.split(". ")
        punchy_sentences = []

        for sentence in sentences:
            # Split long sentences
            if len(sentence.split()) > 15:
                # Find natural break points
                words = sentence.split()
                mid_point = len(words) // 2

                # Look for conjunctions near midpoint
                conjunctions = ["and", "but", "or", "so", "yet", "because"]
                for i in range(max(0, mid_point - 3), min(len(words), mid_point + 3)):
                    if words[i].lower() in conjunctions:
                        first_part = " ".join(words[:i])
                        second_part = " ".join(words[i + 1 :])
                        punchy_sentences.extend([first_part, second_part])
                        break
                else:
                    punchy_sentences.append(sentence)
            else:
                punchy_sentences.append(sentence)

        return ". ".join(punchy_sentences)

    def _balance_sentence_length(self, text: str) -> str:
        """Balance sentence length for professional writing"""
        sentences = text.split(". ")
        balanced_sentences = []

        for sentence in sentences:
            words = sentence.split()

            # If too short, try to combine with context
            if len(words) < 5 and balanced_sentences:
                balanced_sentences[-1] += f", {sentence.lower()}"
            # If too long, consider breaking
            elif len(words) > 25:
                # Look for natural break points
                for i, word in enumerate(words):
                    if (
                        word.lower() in ["however", "therefore", "furthermore", "moreover"]
                        and i > 8
                    ):
                        first_part = " ".join(words[:i])
                        second_part = " ".join(words[i:])
                        balanced_sentences.extend([first_part, second_part])
                        break
                else:
                    balanced_sentences.append(sentence)
            else:
                balanced_sentences.append(sentence)

        return ". ".join(balanced_sentences)

    def get_persona_suggestions(self, channel_id: str, content_topic: str) -> Dict[str, Any]:
        """Get persona - based suggestions for content creation"""
        persona = self.get_persona(channel_id)
        if not persona:
            return {}

        suggestions = {
            "tone_guidance": self._get_tone_guidance(persona.tone_attributes),
            "style_tips": self._get_style_tips(persona.writing_style),
            "vocabulary_level": persona.vocabulary_level.value,
            "suggested_catchphrases": persona.catchphrases[:3],
            "content_format_suggestions": persona.preferred_formats,
            "expertise_angles": self._get_expertise_angles(persona.expertise_areas, content_topic),
            "audience_considerations": persona.target_audience,
        }

        return suggestions

    def _get_tone_guidance(self, tone_attributes: List[str]) -> List[str]:
        """Get guidance for applying tone attributes"""
        guidance = []

        tone_guidance_map = {
            "sarcastic": "Use irony and subtle mockery to make points",
            "witty": "Include clever wordplay and humorous observations",
            "authoritative": "Present information with confidence and expertise",
            "caring": "Show empathy and understanding for the audience",
            "analytical": "Break down complex topics with logical reasoning",
            "inspirational": "Motivate and encourage positive action",
            "conversational": "Write as if speaking directly to a friend",
        }

        for tone in tone_attributes:
            if tone in tone_guidance_map:
                guidance.append(tone_guidance_map[tone])

        return guidance

    def _get_style_tips(self, writing_style: WritingStyle) -> List[str]:
        """Get tips for applying writing style"""
        style_tips_map = {
            WritingStyle.CONVERSATIONAL: [
                "Use contractions and casual language",
                "Ask rhetorical questions to engage readers",
                "Include personal anecdotes when appropriate",
            ],
            WritingStyle.PROFESSIONAL: [
                "Maintain formal tone throughout",
                "Use industry - specific terminology appropriately",
                "Structure content with clear headings and sections",
            ],
            WritingStyle.SATIRICAL: [
                "Use exaggeration for comedic effect",
                "Include ironic observations about current events",
                "Balance humor with substantive points",
            ],
            WritingStyle.INSPIRATIONAL: [
                "Focus on positive outcomes and possibilities",
                "Include success stories and examples",
                "End with actionable steps or encouragement",
            ],
        }

        return style_tips_map.get(writing_style, [])

    def _get_expertise_angles(self, expertise_areas: List[str], topic: str) -> List[str]:
        """Get expertise - based angles for content topic"""
        angles = []

        for area in expertise_areas:
            if area.lower() in topic.lower():
                angles.append(f"Leverage your {area} expertise to provide unique insights")
            else:
                angles.append(f"Connect {topic} to {area} for cross - domain perspective")

        return angles[:3]  # Limit to top 3 suggestions


# Global instance
personas = ChannelPersonas()


def get_personas() -> ChannelPersonas:
    """Get the global Channel Personas instance"""
    return personas
