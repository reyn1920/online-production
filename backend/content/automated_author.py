#!/usr / bin / env python3
"""
Automated Author - Long - Form Content Generation System

This module implements an advanced writing system for creating books and digital products
using "Ghostwriter Persona" and "Checkpointed Writing" protocols. It supports
resumable writing sessions, persona - based writing styles, and structured content generation.

Author: TRAE.AI System
Version: 1.0.0
"""

import hashlib
import json
import logging
import pickle
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import requests

# Import TRAE.AI utilities
try:
    from utils.logger import get_logger
except ImportError:


    def get_logger(name):
        return logging.getLogger(name)

# Import BreakingNewsWatcher for research integration
try:
    from backend.agents.research_tools import BreakingNewsWatcher
except ImportError:
    BreakingNewsWatcher = None


class ContentType(Enum):
    """Types of content that can be generated."""

    BOOK = "book"
    EBOOK = "ebook"
    COURSE = "course"
    GUIDE = "guide"
    MANUAL = "manual"
    WHITEPAPER = "whitepaper"
    BLOG_SERIES = "blog_series"
    NEWSLETTER = "newsletter"


class WritingStage(Enum):
    """Stages of the writing process."""

    OUTLINE = "outline"
    RESEARCH = "research"
    DRAFT = "draft"
    REVISION = "revision"
    EDITING = "editing"
    FINALIZATION = "finalization"


class PersonaType(Enum):
    """Different ghostwriter personas."""

    ACADEMIC = "academic"
    BUSINESS = "business"
    CREATIVE = "creative"
    TECHNICAL = "technical"
    JOURNALISTIC = "journalistic"
    CONVERSATIONAL = "conversational"
    AUTHORITATIVE = "authoritative"
    INSPIRATIONAL = "inspirational"

@dataclass


class GhostwriterPersona:
    """Defines a ghostwriter persona with specific characteristics."""

    name: str
    persona_type: PersonaType
    writing_style: str
    tone: str
    vocabulary_level: str
    sentence_structure: str
    expertise_areas: List[str]
    voice_characteristics: List[str]
    example_phrases: List[str]
    avoid_patterns: List[str]


    def to_prompt(self) -> str:
        """Convert persona to a system prompt."""
        return f"""
You are {self.name}, a {self.persona_type.value} ghostwriter with the following characteristics:

Writing Style: {self.writing_style}
Tone: {self.tone}
Vocabulary Level: {self.vocabulary_level}
Sentence Structure: {self.sentence_structure}

Expertise Areas: {', '.join(self.expertise_areas)}

Voice Characteristics:
{chr(10).join(f'- {char}' for char in self.voice_characteristics)}

Example Phrases You Use:
{chr(10).join(f'- "{phrase}"' for phrase in self.example_phrases)}

Patterns to Avoid:
{chr(10).join(f'- {pattern}' for pattern in self.avoid_patterns)}

Maintain this persona consistently throughout all writing.
"""

@dataclass


class Chapter:
    """Represents a chapter or section in the content."""

    number: int
    title: str
    outline: str
    content: str = ""
    word_count: int = 0
    status: str = "pending"  # pending, in_progress, completed, reviewed
    research_notes: List[str] = field(default_factory = list)
    key_points: List[str] = field(default_factory = list)
    estimated_length: int = 0
    actual_length: int = 0
    last_modified: Optional[datetime] = None

@dataclass


class WritingProject:
    """Represents a complete writing project."""

    title: str
    content_type: ContentType
    target_audience: str
    target_word_count: int
    persona: GhostwriterPersona
    outline: str
    chapters: List[Chapter] = field(default_factory = list)
    research_data: Dict[str, Any] = field(default_factory = dict)
    style_guide: Dict[str, str] = field(default_factory = dict)
    metadata: Dict[str, Any] = field(default_factory = dict)
    current_stage: WritingStage = WritingStage.OUTLINE
    progress_percentage: float = 0.0
    total_word_count: int = 0
    created_at: datetime = field(default_factory = datetime.now)
    last_checkpoint: Optional[datetime] = None
    checkpoint_hash: Optional[str] = None

@dataclass


class WritingCheckpoint:
    """Represents a checkpoint in the writing process."""

    project_id: str
    timestamp: datetime
    stage: WritingStage
    chapter_number: Optional[int]
    content_hash: str
    word_count: int
    progress_data: Dict[str, Any]
    recovery_data: bytes  # Pickled state for recovery


class OllamaClient:
    """Client for interacting with local Ollama LLM."""


    def __init__(
        self, base_url: str = "http://localhost:11434", model: str = "llama3.2"
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.logger = get_logger(self.__class__.__name__)


    def generate(
        self,
            prompt: str,
            system_prompt: Optional[str] = None,
            temperature: float = 0.7,
            max_tokens: int = 4000,
            ) -> str:
        """Generate text using Ollama API."""
        try:
            payload = {
                "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": temperature, "num_predict": max_tokens},
                    }

            if system_prompt:
                payload["system"] = system_prompt

            response = requests.post(
                f"{self.base_url}/api / generate",
                    json = payload,
                    timeout = 180,  # Longer timeout for long - form content
            )
            response.raise_for_status()

            result = response.json()
            return result.get("response", "").strip()

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Ollama API request failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in Ollama generation: {e}")
            raise


class AutomatedAuthor:
    """Main Automated Author class for long - form content generation."""


    def __init__(
        self,
            ollama_url: str = "http://localhost:11434",
            ollama_model: str = "llama3.2",
            checkpoint_dir: str = "./checkpoints",
            ):
        self.ollama = OllamaClient(ollama_url, ollama_model)
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents = True, exist_ok = True)
        self.logger = get_logger(self.__class__.__name__)

        # Built - in personas
        self.personas = self._create_default_personas()

        # Initialize Research Agent for live briefings
        self.research_agent = None
        if BreakingNewsWatcher:
            try:
                self.research_agent = BreakingNewsWatcher()
                self.logger.info("Research Agent initialized for live briefings")
            except Exception as e:
                self.logger.warning(f"Could not initialize Research Agent: {e}")


    def _create_default_personas(self) -> Dict[str, GhostwriterPersona]:
        """Create default ghostwriter personas."""
        return {
            "academic": GhostwriterPersona(
                name="Dr. Alexandra Reed",
                    persona_type = PersonaType.ACADEMIC,
                    writing_style="Scholarly and methodical",
                    tone="Formal and authoritative",
                    vocabulary_level="Advanced academic",
                    sentence_structure="Complex, well - structured sentences with proper citations",
                    expertise_areas=[
                    "Research methodology",
                        "Critical analysis",
                        "Theoretical frameworks",
                        ],
                    voice_characteristics=[
                    "Uses evidence - based arguments",
                        "Employs academic terminology appropriately",
                        "Structures arguments logically",
                        "References credible sources",
                        ],
                    example_phrases=[
                    "The empirical evidence suggests that...",
                        "According to recent research...",
                        "This phenomenon can be understood through the lens of...",
                        "The implications of this finding are significant because...",
                        ],
                    avoid_patterns=[
                    "Overly casual language",
                        "Unsupported claims",
                        "Personal anecdotes without context",
                        ],
                    ),
                "business": GhostwriterPersona(
                name="Marcus Sterling",
                    persona_type = PersonaType.BUSINESS,
                    writing_style="Strategic and results - oriented",
                    tone="Professional and confident",
                    vocabulary_level="Business professional",
                    sentence_structure="Clear, direct sentences with actionable insights",
                    expertise_areas=[
                    "Strategy",
                        "Leadership",
                        "Market analysis",
                        "Operations",
                        ],
                    voice_characteristics=[
                    "Focuses on ROI and business value",
                        "Uses data to support arguments",
                        "Provides actionable recommendations",
                        "Speaks to business outcomes",
                        ],
                    example_phrases=[
                    "The bottom line is...",
                        "This strategy will drive...",
                        "Market data indicates...",
                        "The competitive advantage lies in...",
                        ],
                    avoid_patterns=[
                    "Overly technical jargon",
                        "Theoretical concepts without practical application",
                        "Vague recommendations",
                        ],
                    ),
                "creative": GhostwriterPersona(
                name="Luna Blackwood",
                    persona_type = PersonaType.CREATIVE,
                    writing_style="Imaginative and engaging",
                    tone="Warm and inspiring",
                    vocabulary_level="Rich and varied",
                    sentence_structure="Varied sentence lengths with creative flourishes",
                    expertise_areas=[
                    "Storytelling",
                        "Creative expression",
                        "Emotional engagement",
                        ],
                    voice_characteristics=[
                    "Uses vivid imagery and metaphors",
                        "Creates emotional connections",
                        "Employs narrative techniques",
                        "Balances creativity with clarity",
                        ],
                    example_phrases=[
                    "Imagine a world where...",
                        "Picture this scenario...",
                        "The story unfolds like...",
                        "This reminds me of...",
                        ],
                    avoid_patterns=[
                    "Overly dry or technical language",
                        "Lack of emotional resonance",
                        "Monotonous sentence structure",
                        ],
                    ),
                "technical": GhostwriterPersona(
                name="Dr. Samuel Chen",
                    persona_type = PersonaType.TECHNICAL,
                    writing_style="Precise and systematic",
                    tone="Clear and instructional",
                    vocabulary_level="Technical but accessible",
                    sentence_structure="Step - by - step, logical progression",
                    expertise_areas=[
                    "Technology",
                        "Engineering",
                        "Systems design",
                        "Problem - solving",
                        ],
                    voice_characteristics=[
                    "Explains complex concepts clearly",
                        "Uses examples and analogies",
                        "Provides step - by - step instructions",
                        "Focuses on practical implementation",
                        ],
                    example_phrases=[
                    "Let's break this down step by step...",
                        "The key principle here is...",
                        "To implement this, you would...",
                        "This works because...",
                        ],
                    avoid_patterns=[
                    "Overly complex explanations",
                        "Assumptions about prior knowledge",
                        "Lack of practical examples",
                        ],
                    ),
                }


    def create_project(
        self,
            title: str,
            content_type: ContentType,
            target_audience: str,
            target_word_count: int,
            persona_name: str,
            topic: str,
            key_themes: List[str],
            ) -> WritingProject:
        """Create a new writing project."""
        self.logger.info(f"Creating new project: {title}")

        if persona_name not in self.personas:
            raise ValueError(f"Unknown persona: {persona_name}")

        persona = self.personas[persona_name]

        # Generate initial outline
        outline = self._generate_outline(
            topic, key_themes, content_type, target_word_count, persona
        )

        project = WritingProject(
            title = title,
                content_type = content_type,
                target_audience = target_audience,
                target_word_count = target_word_count,
                persona = persona,
                outline = outline,
                metadata={
                "topic": topic,
                    "key_themes": key_themes,
                    "created_by": "AutomatedAuthor",
                    "version": "1.0.0",
                    },
                )

        # Create chapters from outline
        project.chapters = self._create_chapters_from_outline(
            outline, target_word_count
        )

        # Save initial checkpoint
        self._save_checkpoint(project)

        return project


    def _generate_outline(
        self,
            topic: str,
            key_themes: List[str],
            content_type: ContentType,
            target_word_count: int,
            persona: GhostwriterPersona,
            ) -> str:
        """Generate a detailed outline for the content."""
        self.logger.info("Generating content outline")

        system_prompt = persona.to_prompt()

        prompt = f"""
Create a detailed outline for a {content_type.value} on the topic: "{topic}"

Key Themes to Cover:
{chr(10).join(f'- {theme}' for theme in key_themes)}

Target Word Count: {target_word_count:,} words
Content Type: {content_type.value}

Create a comprehensive outline that:
1. Has a logical flow and structure
2. Covers all key themes thoroughly
3. Is appropriate for the target word count
4. Includes chapter / section titles and brief descriptions
5. Maintains your persona's expertise and style
6. Provides clear learning objectives or value propositions

Format the outline with clear headings and subheadings.

Outline:
"""

        return self.ollama.generate(prompt, system_prompt, temperature = 0.6)


    def _generate_script_content(
        self, topic: str, style: str = "professional", duration: int = 60
    ) -> str:
        """Generate script content for video / audio production.

        Args:
            topic: The main topic for the script
            style: Writing style (professional, casual, educational, etc.)
            duration: Target duration in seconds

        Returns:
            Generated script content
        """
        try:
            # Estimate words based on duration (average 150 words per minute)
            target_words = int((duration / 60) * 150)

            # Select appropriate persona based on style
            persona_map = {
                "professional": "business",
                    "casual": "conversational",
                    "educational": "academic",
                    "creative": "creative",
                    "technical": "technical",
                    "inspirational": "inspirational",
                    }

            persona_name = persona_map.get(style.lower(), "conversational")
            persona = self.personas.get(persona_name, self.personas["conversational"])

            system_prompt = f"""
You are {persona.name}, a {persona.persona_type.value} content creator.

Writing Style: {persona.writing_style}
Tone: {persona.tone}
Vocabulary: {persona.vocabulary_level}

Your task is to create an engaging script for a {duration}-second presentation.
Target approximately {target_words} words.

Characteristics:
{chr(10).join(f'• {char}' for char in persona.voice_characteristics)}

Example phrases you might use:
{chr(10).join(f'• "{phrase}"' for phrase in persona.example_phrases[:3])}

Avoid:
{chr(10).join(f'• {pattern}' for pattern in persona.avoid_patterns[:3])}
"""

            prompt = f"""
Create an engaging {duration}-second script about: {topic}

Style: {style}
Target length: {target_words} words

The script should:
1. Have a compelling opening hook
2. Present key information clearly and engagingly
3. Include natural transitions
4. End with a strong conclusion or call - to - action
5. Be suitable for video / audio presentation
6. Match the requested style and tone
7. Be exactly the right length for the time duration

Script:
"""

            script_content = self.ollama.generate(
                prompt = prompt,
                    system_prompt = system_prompt,
                    temperature = 0.7,
                    max_tokens = min(target_words * 2, 2000),
                    )

            return script_content.strip()

        except Exception as e:
            self.logger.error(f"Error generating script content: {e}")
            # Return fallback content
            return f"""Welcome to our {style} presentation about {topic}.

In this {duration}-second segment, we'll explore the key aspects of {topic} and provide valuable insights.

Let's dive into the main points:
1. Introduction to {topic}
2. Key benefits and applications
3. Important considerations
4. Next steps and recommendations

Thank you for your attention. We hope this information about {topic} has been valuable and informative."""


    def _get_live_topic_briefing(self, topic: str, key_themes: List[str]) -> str:
        """Get live briefing from Research Agent for enhanced content generation."""
        if not self.research_agent:
            return ""

        try:
            self.logger.info(f"Fetching live briefing for topic: {topic}")

            # Get latest intelligence briefing
            briefing = self.research_agent.get_latest_intelligence_briefing()

            # Get trending topics related to our content
            trending_topics = self.research_agent.get_trending_keywords()

            # Get topic - specific headlines
            topic_headlines = self.research_agent.get_topic_headlines(topic, limit = 10)

            # Check for hypocrisy content opportunities
            hypocrisy_opportunities = []
            if hasattr(self.research_agent, "get_hypocrisy_content_opportunities"):
                hypocrisy_opportunities = (
                    self.research_agent.get_hypocrisy_content_opportunities(topic)
                )

            # Compile live briefing
            live_briefing = f"""
=== LIVE TOPIC BRIEFING ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Topic: {topic}

--- LATEST INTELLIGENCE ---
{briefing.get('summary', 'No recent intelligence available')}

--- TRENDING TOPICS ---
"""

            for trend in trending_topics[:5]:  # Top 5 trends
                live_briefing += f"• {trend.get('topic', 'Unknown')}: {trend.get('momentum_score', 0):.2f} momentum\n"

            live_briefing += "\n--- RECENT HEADLINES ---\n"
            for headline in topic_headlines[:8]:  # Top 8 headlines
                live_briefing += f"• {headline.get('title', 'No title')} ({headline.get('source', 'Unknown source')})\n"

            if hypocrisy_opportunities:
                live_briefing += "\n--- HYPOCRISY OPPORTUNITIES ---\n"
                for opp in hypocrisy_opportunities[:3]:  # Top 3 opportunities
                    live_briefing += f"• {opp.get('topic', 'Unknown')}: {opp.get('description', 'No description')}\n"

            live_briefing += "\n--- CONTENT ANGLES ---\n"
            for theme in key_themes:
                live_briefing += f"• Consider {theme} in context of current events\n"

            live_briefing += "\n=== END BRIEFING ===\n"

            self.logger.info("Live briefing compiled successfully")
            return live_briefing

        except Exception as e:
            self.logger.error(f"Error fetching live briefing: {e}")
            return ""


    def _create_chapters_from_outline(
        self, outline: str, target_word_count: int
    ) -> List[Chapter]:
        """Extract chapters from the generated outline."""
        # Simple parsing - in production, this could be more sophisticated
        lines = outline.split("\n")
        chapters = []
        current_chapter = None
        chapter_num = 0

        estimated_words_per_chapter = target_word_count // max(
            1,
                len(
                [l for l in lines if l.strip().startswith(("Chapter", "Section", "#"))]
            ),
                )

        for line in lines:
            line = line.strip()
            if line.startswith(("Chapter", "Section", "#")) and ":" in line:
                if current_chapter:
                    chapters.append(current_chapter)

                chapter_num += 1
                title = line.split(":", 1)[1].strip() if ":" in line else line
                current_chapter = Chapter(
                    number = chapter_num,
                        title = title,
                        outline = line,
                        estimated_length = estimated_words_per_chapter,
                        )
            elif current_chapter and line:
                current_chapter.outline += f"\n{line}"

        if current_chapter:
            chapters.append(current_chapter)

        # If no chapters found, create a default structure
        if not chapters:
            chapters = [
                Chapter(
                    number = 1,
                        title="Introduction",
                        outline="Introduction to the topic",
                        estimated_length = target_word_count // 3,
                        ),
                    Chapter(
                    number = 2,
                        title="Main Content",
                        outline="Core content and analysis",
                        estimated_length = target_word_count // 3,
                        ),
                    Chapter(
                    number = 3,
                        title="Conclusion",
                        outline="Summary and final thoughts",
                        estimated_length = target_word_count // 3,
                        ),
                    ]

        return chapters


    def write_chapter(
        self,
            project: WritingProject,
            chapter_number: int,
            research_context: Optional[str] = None,
            ) -> str:
        """Write a specific chapter using Ghostwriter Persona and Checkpointed Writing protocols."""
        if chapter_number > len(project.chapters):
            raise ValueError(f"Chapter {chapter_number} does not exist")

        chapter = project.chapters[chapter_number - 1]
        self.logger.info(f"Writing chapter {chapter_number}: {chapter.title}")

        # Create checkpoint before writing (Checkpointed Writing Protocol)
        checkpoint_name = f"pre_chapter_{chapter_number}"
        self._save_checkpoint(project)

        chapter.status = "in_progress"

        # Get live briefing for enhanced content generation
        topic = f"{project.title} {chapter.title}"
        key_themes = (
            chapter.key_points
            if isinstance(chapter.key_points, list)
            else [chapter.key_points]
        )
        live_briefing = self._get_live_topic_briefing(topic, key_themes)

        # Apply Ghostwriter Persona with enhanced context
        system_prompt = self._build_enhanced_persona_prompt(project, chapter_number)

        # Build comprehensive context from previous chapters
        previous_context = self._build_chapter_context(project, chapter_number)

        research_section = ""
        if research_context:
            research_section = f"""
Research Context:
{research_context}

Incorporate relevant research findings naturally into the content while maintaining your persona's voice.
"""

        # Add live briefing section
        briefing_section = ""
        if live_briefing:
            briefing_section = f"""
{live_briefing}

Use the live briefing information to make the content more current, relevant, and engaging while maintaining your persona's voice.
"""

        prompt = f"""
Write Chapter {chapter.number}: "{chapter.title}" for the {project.content_type.value} titled "{project.title}"

Chapter Outline:
{chapter.outline}

Target Audience: {project.target_audience}
Target Length: {chapter.estimated_length:,} words

{previous_context}

{research_section}

{briefing_section}

Project Overview:
{project.outline}

As {project.persona.name}, write engaging, high - quality content that:
1. Follows the chapter outline precisely
2. Maintains your established persona and voice consistently
3. Provides exceptional value to the target audience
4. Flows naturally from previous content
5. Includes practical examples and actionable insights
6. Uses current events and trending topics when relevant
7. Meets the target word count
7. Uses proper formatting and structure
8. Incorporates your expertise areas naturally
9. Avoids patterns you typically avoid
10. Uses your characteristic phrases and voice

Chapter Content:
"""

        try:
            # Generate chapter content with enhanced error handling
            content = self._write_chapter_with_segments(prompt, system_prompt, chapter)

            # Update chapter with validation
            chapter.content = content
            chapter.word_count = len(content.split())
            chapter.actual_length = chapter.word_count
            chapter.status = "completed"
            chapter.last_modified = datetime.now()

            # Update project progress
            self._update_project_progress(project)

            # Save checkpoint after successful completion
            self._save_checkpoint(project)

            self.logger.info(
                f"Chapter {chapter_number} completed: {chapter.word_count} words"
            )
            return content

        except Exception as e:
            self.logger.error(f"Error writing chapter {chapter_number}: {e}")
            # Restore chapter status on failure
            chapter.status = "pending"
            raise


    def write_complete_project(
        self, project: WritingProject, research_data: Optional[Dict[str, str]] = None
    ) -> WritingProject:
        """Write the complete project using Checkpointed Writing protocol."""
        self.logger.info(f"Starting complete project writing: {project.title}")

        try:
            # Save initial checkpoint
            self._save_checkpoint(project)

            for i, chapter in enumerate(project.chapters, 1):
                if chapter.status != "completed":
                    self.logger.info(
                        f"Writing chapter {i}/{len(project.chapters)}: {chapter.title}"
                    )

                    research_context = None
                    if research_data and str(i) in research_data:
                        research_context = research_data[str(i)]

                    # Write chapter with enhanced error handling
                    try:
                        self.write_chapter(project, i, research_context)

                        # Progress update after each chapter
                        self.logger.info(
                            f"Chapter {i} completed. Project progress: {project.progress_percentage:.1f}%"
                        )

                    except Exception as chapter_error:
                        self.logger.error(
                            f"Failed to write chapter {i}: {chapter_error}"
                        )
                        # Continue with next chapter rather than failing entire project
                        chapter.status = "failed"
                        continue

                    # Adaptive pause based on chapter length
                    pause_time = min(5, max(2, chapter.word_count // 1000))
                    time.sleep(pause_time)

            # Update project stage and final metrics
            project.current_stage = WritingStage.DRAFT
            self._update_project_progress(project)

            # Final checkpoint
            self._save_checkpoint(project)

            completed_chapters = sum(
                1 for c in project.chapters if c.status == "completed"
            )
            self.logger.info(
                f"Project writing completed: {completed_chapters}/{len(project.chapters)} chapters, {project.total_word_count:,} words"
            )

            return project

        except Exception as e:
            self.logger.error(f"Project writing failed: {e}")
            # Save checkpoint before raising
            self._save_checkpoint(project)
            raise


    def _update_project_progress(self, project: WritingProject) -> None:
        """Update project progress metrics."""
        completed_chapters = sum(1 for c in project.chapters if c.status == "completed")
        total_chapters = len(project.chapters)

        project.progress_percentage = (
            (completed_chapters / total_chapters) * 100 if total_chapters > 0 else 0
        )
        project.total_word_count = sum(c.word_count for c in project.chapters)


    def _apply_ghostwriter_persona(self, project: WritingProject) -> str:
        """Apply Ghostwriter Persona protocols for enhanced writing."""
        persona = project.persona

        ghostwriter_prompt = f"""
        GHOSTWRITER PERSONA ACTIVATION:

        You are {persona.name}, a {persona.persona_type.value} with the following expertise:
        - Primary Areas: {', '.join(persona.expertise_areas)}
        - Writing Style: {persona.writing_style}
        - Target Audience: {project.target_audience}

        PERSONA CHARACTERISTICS:
        - Voice: {persona.voice_characteristics}
        - Tone: {persona.tone}
        - Vocabulary Level: {persona.vocabulary_level}

        WRITING PROTOCOLS:
        1. Maintain consistent voice throughout all content
        2. Draw from your expertise areas naturally
        3. Use your characteristic phrases and expressions
        4. Avoid patterns that don't align with your persona
        5. Provide value through your unique perspective
        6. Adapt tone appropriately for the target audience

        Remember: You are not just writing content, you are embodying {persona.name}'s expertise and voice.
        """

        return ghostwriter_prompt


    def _create_fallback_outline(self, project: WritingProject) -> List[Chapter]:
        """Create a fallback outline structure when outline parsing fails."""
        chapters = []
        chapters_count = max(
            8, min(15, project.target_word_count // 3000)
        )  # Adaptive chapter count
        words_per_chapter = project.target_word_count // chapters_count

        for i in range(chapters_count):
            chapter = Chapter(
                number = i + 1,
                    title = f"Chapter {i + 1}",
                    outline = f"Chapter {i + 1} content for {project.title}",
                    content="",
                    word_count = 0,
                    status="pending",
                    estimated_length = words_per_chapter,
                    )
            chapters.append(chapter)

        return chapters


    def _write_chapter_segments(
        self, prompt: str, system_prompt: str, chapter: Chapter
    ) -> str:
        """Write chapter content in segments for better quality control."""
        target_words = chapter.estimated_length

        if target_words <= 2000:
            # Single segment for shorter chapters
            response = self.ollama.generate(
                prompt, system_prompt, temperature = 0.7, max_tokens = 4000
            )
            return response
        else:
            # Multiple segments for longer chapters
            segments = []
            num_segments = max(2, target_words // 1500)
            words_per_segment = target_words // num_segments

            for i in range(num_segments):
                segment_prompt = f"""
                {prompt}

                SEGMENT INSTRUCTIONS:
                - This is segment {i + 1} of {num_segments}
                - Target length: approximately {words_per_segment} words
                - {'Continue naturally from previous content' if i > 0 else 'Begin the chapter with a strong opening'}
                - {'Build toward the chapter conclusion' if i == num_segments - 1 else 'Develop the narrative and maintain engagement'}
                """

                segment_content = self.ollama.generate(
                    segment_prompt, system_prompt, temperature = 0.7, max_tokens = 3000
                )
                segments.append(segment_content)

                # Brief pause between segments
                time.sleep(1)

            return "\n\n".join(segments)


    def _restore_from_checkpoint(
        self, project: WritingProject, checkpoint_name: str
    ) -> bool:
        """Restore project state from a specific checkpoint."""
        try:
            # This is a simplified implementation
            # In a full implementation, you would restore from the actual checkpoint file
            self.logger.info(
                f"Attempting to restore from checkpoint: {checkpoint_name}"
            )

            # For now, just reset the current chapter status
            for chapter in project.chapters:
                if chapter.status == "in_progress":
                    chapter.status = "pending"
                    chapter.content = ""
                    chapter.word_count = 0

            return True

        except Exception as e:
            self.logger.error(
                f"Failed to restore from checkpoint {checkpoint_name}: {e}"
            )
            return False


    def _save_checkpoint(self, project: WritingProject) -> None:
        """Save a checkpoint using Checkpointed Writing protocol."""
        try:
            project_id = hashlib.md5(
                f"{project.title}_{project.created_at}".encode()
            ).hexdigest()[:8]

            # Enhanced checkpoint data with recovery information
            checkpoint_data = {
                "project": asdict(project),
                    "timestamp": datetime.now().isoformat(),
                    "checkpoint_type": "automated_author",
                    "version": "1.0.0",
                    "recovery_metadata": {
                    "total_chapters": len(project.chapters),
                        "completed_chapters": sum(
                        1 for c in project.chapters if c.status == "completed"
                    ),
                        "current_stage": project.current_stage.value,
                        "persona_type": project.persona.persona_type.value,
                        },
                    }

            # Calculate content hash for integrity
            content_str = json.dumps(checkpoint_data, sort_keys = True, default = str)
            content_hash = hashlib.sha256(content_str.encode()).hexdigest()[:16]

            # Create comprehensive checkpoint
            checkpoint = WritingCheckpoint(
                project_id = project_id,
                    timestamp = datetime.now(),
                    stage = project.current_stage,
                    chapter_number = self._get_current_chapter_number(project),
                    content_hash = content_hash,
                    word_count = project.total_word_count,
                    progress_data = checkpoint_data,
                    recovery_data = pickle.dumps(project),
                    )

            # Save with timestamp for better organization
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            checkpoint_file = (
                self.checkpoint_dir
                / f"{project_id}_{timestamp_str}_{content_hash}.checkpoint"
            )

            with open(checkpoint_file, "wb") as f:
                pickle.dump(checkpoint, f)

            # Also save a JSON version for human readability
            json_file = self.checkpoint_dir / f"{project_id}_{timestamp_str}.json"
            with open(json_file, "w", encoding="utf - 8") as f:
                json.dump(checkpoint_data, f, indent = 2, default = str)

            project.last_checkpoint = checkpoint.timestamp
            project.checkpoint_hash = content_hash

            self.logger.info(f"Checkpoint saved: {checkpoint_file}")

        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {e}")


    def _get_current_chapter_number(self, project: WritingProject) -> Optional[int]:
        """Get the current chapter being worked on."""
        for chapter in project.chapters:
            if chapter.status == "in_progress":
                return chapter.number
        return None


    def _build_enhanced_persona_prompt(
        self, project: WritingProject, chapter_number: int
    ) -> str:
        """Build enhanced persona prompt with chapter - specific context."""
        base_prompt = project.persona.to_prompt()

        chapter_context = f"""

CHAPTER - SPECIFIC CONTEXT:
You are now writing Chapter {chapter_number} of {len(project.chapters)} total chapters.
Project Progress: {project.progress_percentage:.1f}% complete
Current Stage: {project.current_stage.value}

Maintain consistency with your established voice while adapting to the specific needs of this chapter.
"""

        return base_prompt + chapter_context


    def _build_chapter_context(
        self, project: WritingProject, chapter_number: int
    ) -> str:
        """Build comprehensive context from previous chapters."""
        if chapter_number <= 1:
            return "This is the opening chapter. Set the tone and establish the foundation for the entire work."

        prev_chapters = [c for c in project.chapters[: chapter_number - 1] if c.content]
        if not prev_chapters:
            return "Previous chapters are not yet available. Write this chapter to stand alone while fitting the overall outline."

        context = "PREVIOUS CHAPTERS CONTEXT:\n"
        for chapter in prev_chapters[-3:]:  # Last 3 chapters for context
            word_count = len(chapter.content.split())
            context += (
                f"\nChapter {chapter.number}: {chapter.title} ({word_count} words)\n"
            )
            # Add brief summary of key points
            if len(chapter.content) > 500:
                context += f"Key themes: {chapter.content[:500]}...\n"

        context += (
            "\nMaintain consistency with established themes, tone, and narrative flow."
        )
        return context


    def _write_chapter_with_segments(
        self, prompt: str, system_prompt: str, chapter: Chapter
    ) -> str:
        """Write chapter content with improved segmentation for better quality."""
        # For longer chapters, break into segments
        if chapter.estimated_length > 3000:
            return self._write_long_chapter_segments(prompt, system_prompt, chapter)
        else:
            return self.ollama.generate(
                prompt, system_prompt, temperature = 0.7, max_tokens = 6000
            )


    def _write_long_chapter_segments(
        self, prompt: str, system_prompt: str, chapter: Chapter
    ) -> str:
        """Write long chapters in segments for better coherence."""
        segments = []
        target_segments = max(
            2, chapter.estimated_length // 2000
        )  # ~2000 words per segment

        for i in range(target_segments):
            segment_prompt = f"""{prompt}

Write segment {i + 1} of {target_segments} for this chapter.
Target length for this segment: ~{chapter.estimated_length // target_segments} words.
{"Continue from the previous segment naturally." if i > 0 else "Begin the chapter."}
"""

            segment_content = self.ollama.generate(
                segment_prompt, system_prompt, temperature = 0.7, max_tokens = 3000
            )
            segments.append(segment_content)

            # Brief pause between segments
            time.sleep(1)

        return "\n\n".join(segments)


    def load_checkpoint(
        self, project_id: str, checkpoint_hash: Optional[str] = None
    ) -> WritingProject:
        """Load a project from checkpoint with enhanced recovery."""
        try:
            if checkpoint_hash:
                # Look for specific checkpoint
                checkpoints = list(
                    self.checkpoint_dir.glob(
                        f"{project_id}_ * _{checkpoint_hash}.checkpoint"
                    )
                )
                if not checkpoints:
                    raise FileNotFoundError(
                        f"Checkpoint with hash {checkpoint_hash} not found for project {project_id}"
                    )
                checkpoint_file = checkpoints[0]
            else:
                # Find latest checkpoint for project
                checkpoints = list(
                    self.checkpoint_dir.glob(f"{project_id}_*.checkpoint")
                )
                if not checkpoints:
                    raise FileNotFoundError(
                        f"No checkpoints found for project {project_id}"
                    )
                checkpoint_file = max(checkpoints, key = lambda p: p.stat().st_mtime)

            with open(checkpoint_file, "rb") as f:
                checkpoint = pickle.load(f)

            # Validate checkpoint integrity
            if not self._validate_checkpoint(checkpoint):
                raise ValueError(f"Checkpoint validation failed: {checkpoint_file}")

            project = pickle.loads(checkpoint.recovery_data)

            # Log recovery information
            recovery_info = checkpoint.progress_data.get("recovery_metadata", {})
            self.logger.info(f"Project loaded from checkpoint: {checkpoint_file}")
            self.logger.info(
                f"Recovery info - Chapters: {recovery_info.get('completed_chapters', 0)}/{recovery_info.get('total_chapters', 0)}, Stage: {recovery_info.get('current_stage', 'unknown')}"
            )

            return project

        except Exception as e:
            self.logger.error(f"Failed to load checkpoint: {e}")
            raise


    def _validate_checkpoint(self, checkpoint: WritingCheckpoint) -> bool:
        """Validate checkpoint integrity."""
        try:
            # Basic validation checks
            if not checkpoint.recovery_data:
                return False

            # Try to deserialize the project data
            project = pickle.loads(checkpoint.recovery_data)

            # Validate essential project attributes
            required_attrs = ["title", "content_type", "persona", "chapters"]
            for attr in required_attrs:
                if not hasattr(project, attr):
                    return False

            return True

        except Exception:
            return False


    def list_checkpoints(
        self, project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List available checkpoints."""
        try:
            if project_id:
                pattern = f"{project_id}_*.checkpoint"
            else:
                pattern = "*.checkpoint"

            checkpoints = []
            for checkpoint_file in self.checkpoint_dir.glob(pattern):
                try:
                    with open(checkpoint_file, "rb") as f:
                        checkpoint = pickle.load(f)

                    recovery_metadata = checkpoint.progress_data.get(
                        "recovery_metadata", {}
                    )

                    checkpoints.append(
                        {
                            "file": checkpoint_file.name,
                                "project_id": checkpoint.project_id,
                                "timestamp": checkpoint.timestamp,
                                "stage": checkpoint.stage.value,
                                "word_count": checkpoint.word_count,
                                "completed_chapters": recovery_metadata.get(
                                "completed_chapters", 0
                            ),
                                "total_chapters": recovery_metadata.get(
                                "total_chapters", 0
                            ),
                                "content_hash": checkpoint.content_hash,
                                }
                    )

                except Exception as e:
                    self.logger.warning(
                        f"Could not read checkpoint {checkpoint_file}: {e}"
                    )
                    continue

            # Sort by timestamp, newest first
            checkpoints.sort(key = lambda x: x["timestamp"], reverse = True)
            return checkpoints

        except Exception as e:
            self.logger.error(f"Failed to list checkpoints: {e}")
            return []


    def export_project(
        self, project: WritingProject, output_path: str, format_type: str = "markdown"
    ) -> None:
        """Export the completed project to various formats."""
        try:
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents = True, exist_ok = True)

            if format_type.lower() == "markdown":
                self._export_markdown(project, output_path)
            elif format_type.lower() == "json":
                self._export_json(project, output_path)
            elif format_type.lower() == "txt":
                self._export_text(project, output_path)
            else:
                raise ValueError(f"Unsupported format: {format_type}")

            self.logger.info(f"Project exported to {output_path}")

        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            raise


    def _export_markdown(self, project: WritingProject, output_path: str) -> None:
        """Export project as Markdown."""
        with open(output_path, "w", encoding="utf - 8") as f:
            f.write(f"# {project.title}\n\n")
            f.write(f"**Content Type:** {project.content_type.value}\n")
            f.write(f"**Target Audience:** {project.target_audience}\n")
            f.write(f"**Word Count:** {project.total_word_count:,}\n")
            f.write(
                f"**Generated by:** {project.persona.name} ({project.persona.persona_type.value})\n\n"
            )

            f.write("## Outline\n\n")
            f.write(f"{project.outline}\n\n")

            for chapter in project.chapters:
                f.write(f"## Chapter {chapter.number}: {chapter.title}\n\n")
                if chapter.content:
                    f.write(f"{chapter.content}\n\n")
                else:
                    f.write("*[Content not yet generated]*\n\n")


    def _export_json(self, project: WritingProject, output_path: str) -> None:
        """Export project as JSON."""
        with open(output_path, "w", encoding="utf - 8") as f:
            json.dump(asdict(project), f, indent = 2, default = str)


    def _export_text(self, project: WritingProject, output_path: str) -> None:
        """Export project as plain text."""
        with open(output_path, "w", encoding="utf - 8") as f:
            f.write(f"{project.title}\n")
            f.write("=" * len(project.title) + "\n\n")

            for chapter in project.chapters:
                f.write(f"Chapter {chapter.number}: {chapter.title}\n")
                f.write("-" * (len(chapter.title) + 20) + "\n\n")
                if chapter.content:
                    f.write(f"{chapter.content}\n\n")

# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level = logging.INFO)

    # Create AutomatedAuthor instance
    author = AutomatedAuthor()

    # Example project creation
    try:
        project = author.create_project(
            title="The Complete Guide to Machine Learning",
                content_type = ContentType.GUIDE,
                target_audience="Software developers and data scientists",
                target_word_count = 15000,
                persona_name="technical",
                topic="Machine Learning Fundamentals and Applications",
                key_themes=[
                "Introduction to ML concepts",
                    "Types of machine learning",
                    "Popular algorithms and techniques",
                    "Real - world applications",
                    "Best practices and implementation",
                    ],
                )

        print(f"Project created: {project.title}")
        print(f"Chapters: {len(project.chapters)}")
        print(f"Target word count: {project.target_word_count:,}")
        print(f"Persona: {project.persona.name}")

        # Write first chapter as example
        first_chapter = author.write_chapter(project, 1)
        print(f"\nFirst chapter written: {len(first_chapter.split())} words")

        # Export project
        author.export_project(project, "./output / ml_guide.md", "markdown")
        print("Project exported successfully")

    except Exception as e:
        print(f"Error: {e}")
