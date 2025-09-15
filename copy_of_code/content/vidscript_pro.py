#!/usr/bin/env python3
""""""
VidScriptPro Framework - AI - Powered Multi - Stage Scriptwriting System

This module provides a comprehensive scriptwriting framework that uses local Ollama LLM
for generating professional video scripts through a structured multi - stage process:
    pass
1. Logline Development
2. Synopsis Creation
3. Character Development
4. Scene Breakdown
5. Full Script Generation

Author: TRAE.AI Content Generation System
Version: 1.0.0
""""""

import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ScriptElement:
    """Base class for script elements."""

    content: str
    timestamp: datetime
    stage: str
    metadata: Dict[str, Any]


@dataclass
class Character:
    """Character definition for script."""

    name: str
    description: str
    personality: str
    background: str
    motivation: str
    arc: str


@dataclass
class Scene:
    """Scene structure for script."""

    number: int
    location: str
    time_of_day: str
    characters: List[str]
    description: str
    dialogue: List[Dict[str, str]]
    action: List[str]
    duration_estimate: int  # in seconds


@dataclass
class Script:
    """Complete script structure."""

    title: str
    logline: str
    synopsis: str
    characters: List[Character]
    scenes: List[Scene]
    total_duration: int
    genre: str
    target_audience: str
    created_at: datetime
    version: str


class OllamaLLMClient:
    """Client for interacting with local Ollama LLM server."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        self.base_url = base_url
        self.model = model
        self.session = requests.Session()
        self.session.timeout = 120  # 2 minute timeout

    def generate(self, prompt: str, system_prompt: str = "", max_tokens: int = 2000) -> str:
        """Generate text using Ollama LLM."""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.7,
                    "top_p": 0.9,
# BRACKET_SURGEON: disabled
#                 },
# BRACKET_SURGEON: disabled
#             }

            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                headers={"Content - Type": "application/json"},
# BRACKET_SURGEON: disabled
#             )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return ""

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error in LLM generation: {e}")
            return ""

    def health_check(self) -> bool:
        """Check if Ollama server is running and accessible."""
        try:
            response = self.session.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False


class VidScriptPro:
    """Advanced AI - powered scriptwriting framework."""

    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama2"):
        self.llm = OllamaLLMClient(ollama_url, model)
        self.current_project: Optional[Dict[str, Any]] = None
        self.script_templates = self._load_script_templates()

        # Verify Ollama connection
        if not self.llm.health_check():
            logger.warning("Ollama server not accessible. Some features may not work.")

    def _load_script_templates(self) -> Dict[str, str]:
        """Load scriptwriting templates and prompts."""
        return {
            "logline_prompt": """"""
You are a professional screenwriter. Create a compelling logline for a video script.

A logline is a one - sentence summary that captures:
- The protagonist
- The central conflict
- The stakes
- The genre/tone

Topic: {topic}
Genre: {genre}
Target Duration: {duration} minutes
Target Audience: {audience}

Write a single, powerful logline that would make someone want to watch this video.
""","""
            "synopsis_prompt": """"""
You are a professional screenwriter. Expand the following logline into a detailed synopsis.

Logline: {logline}

Create a 3 - 4 paragraph synopsis that includes:
- Setup and character introduction
- Rising action and key conflicts
- Climax and resolution
- Emotional journey and themes

Keep it engaging and visual, suitable for a {duration}-minute video.
""","""
            "character_prompt": """"""
You are a professional character developer. Create detailed character profiles for this script.

Synopsis: {synopsis}
Genre: {genre}

For each main character, provide:
- Name and brief description
- Personality traits (3 - 4 key traits)
- Background and motivation
- Character arc throughout the story

Focus on characters that will drive the narrative forward.
""","""
            "scene_breakdown_prompt": """"""
You are a professional screenwriter. Break down this story into scenes.

Synopsis: {synopsis}
Characters: {characters}
Target Duration: {duration} minutes

Create a scene - by - scene breakdown with:
- Scene number and location
- Time of day
- Characters present
- Brief scene description
- Key dialogue points
- Estimated duration

Aim for {target_scenes} scenes total.
""","""
            "script_prompt": """"""
You are a professional screenwriter. Write the full script for this scene.

Scene Details:
{scene_details}

Characters:
{characters}

Write in proper screenplay format with:
- Scene headers (INT./EXT. LOCATION - TIME)
- Action lines (present tense, visual)
- Character names (CAPS)
- Dialogue (natural, character - specific)
- Parentheticals when needed

Make it engaging, visual, and true to the characters.
""","""
# BRACKET_SURGEON: disabled
#         }

    def create_logline(
        self,
        topic: str,
        genre: str = "Drama",
        duration: int = 10,
        audience: str = "General",
# BRACKET_SURGEON: disabled
#     ) -> str:
        """Generate a compelling logline for the video script."""
        logger.info(f"Creating logline for topic: {topic}")

        prompt = self.script_templates["logline_prompt"].format(
            topic=topic, genre=genre, duration=duration, audience=audience
# BRACKET_SURGEON: disabled
#         )

        system_prompt = "You are an expert screenwriter specializing in compelling loglines."

        logline = self.llm.generate(prompt, system_prompt, max_tokens=200)

        if not logline:
            logger.error("Failed to generate logline")
            return f"A {genre.lower()} story about {topic}."

        return logline

    def create_synopsis(self, logline: str, duration: int = 10) -> str:
        """Expand logline into detailed synopsis."""
        logger.info("Creating synopsis from logline")

        prompt = self.script_templates["synopsis_prompt"].format(logline=logline, duration=duration)

        system_prompt = "You are an expert story developer who creates engaging synopses."

        synopsis = self.llm.generate(prompt, system_prompt, max_tokens=800)

        if not synopsis:
            logger.error("Failed to generate synopsis")
            return f"A story based on: {logline}"

        return synopsis

    def develop_characters(self, synopsis: str, genre: str = "Drama") -> List[Character]:
        """Create detailed character profiles."""
        logger.info("Developing characters")

        prompt = self.script_templates["character_prompt"].format(synopsis=synopsis, genre=genre)

        system_prompt = "You are an expert character developer who creates compelling, three - dimensional characters."

        character_text = self.llm.generate(prompt, system_prompt, max_tokens=1000)

        if not character_text:
            logger.error("Failed to generate characters")
            return [
                Character(
                    name="Protagonist",
                    description="Main character",
                    personality="Determined, complex",
                    background="Unknown",
                    motivation="To overcome challenges",
                    arc="Growth through adversity",
# BRACKET_SURGEON: disabled
#                 )
# BRACKET_SURGEON: disabled
#             ]

        # Parse character text into Character objects
        characters = self._parse_characters(character_text)
        return characters

    def _parse_characters(self, character_text: str) -> List[Character]:
        """Parse LLM - generated character text into Character objects."""
        characters = []

        # Simple parsing - look for character sections
        sections = character_text.split("\\n\\n")

        for section in sections:
            if len(section.strip()) < 20:  # Skip short sections
                continue

            lines = [line.strip() for line in section.split("\\n") if line.strip()]

            if len(lines) >= 2:
                # Extract character name (usually first line)
                name_line = lines[0]
                name = name_line.split(":")[0].strip() if ":" in name_line else name_line
                name = name.replace("**", "").replace("#", "").strip()"

                # Combine remaining lines as description
                description = " ".join(lines[1:])[:200]  # Limit length

                character = Character(
                    name=name,
                    description=description,
                    personality="Complex, multi - dimensional",
                    background="Developed through story context",
                    motivation="Drives narrative forward",
                    arc="Evolves throughout story",
# BRACKET_SURGEON: disabled
#                 )
                characters.append(character)

        # Ensure at least one character
        if not characters:
            characters.append(
                Character(
                    name="Main Character",
                    description="Primary protagonist of the story",
                    personality="Engaging, relatable",
                    background="Contextually appropriate",
                    motivation="Story - driven goals",
                    arc="Meaningful character growth",
# BRACKET_SURGEON: disabled
#                 )
# BRACKET_SURGEON: disabled
#             )

        return characters[:4]  # Limit to 4 main characters

    def create_scene_breakdown(
        self, synopsis: str, characters: List[Character], duration: int = 10
    ) -> List[Scene]:
        """Break story into scenes."""
        logger.info("Creating scene breakdown")

        target_scenes = max(3, duration // 2)  # Rough estimate
        character_names = [char.name for char in characters]

        prompt = self.script_templates["scene_breakdown_prompt"].format(
            synopsis=synopsis,
            characters=", ".join(character_names),
            duration=duration,
            target_scenes=target_scenes,
# BRACKET_SURGEON: disabled
#         )

        system_prompt = (
            "You are an expert script supervisor who creates well - paced scene breakdowns."
# BRACKET_SURGEON: disabled
#         )

        scene_text = self.llm.generate(prompt, system_prompt, max_tokens=1200)

        if not scene_text:
            logger.error("Failed to generate scene breakdown")
            return self._create_default_scenes(duration)

        scenes = self._parse_scenes(scene_text, character_names, duration)
        return scenes

    def _create_default_scenes(self, duration: int) -> List[Scene]:
        """Create default scene structure if LLM fails."""
        num_scenes = max(3, duration // 3)
        scenes = []

        for i in range(num_scenes):
            scene = Scene(
                number=i + 1,
                location="LOCATION",
                time_of_day="DAY",
                characters=["MAIN CHARACTER"],
                description=f"Scene {i + 1} description",
                dialogue=[],
                action=["Action description"],
                duration_estimate=duration * 60 // num_scenes,
# BRACKET_SURGEON: disabled
#             )
            scenes.append(scene)

        return scenes

    def _parse_scenes(
        self, scene_text: str, character_names: List[str], total_duration: int
    ) -> List[Scene]:
        """Parse LLM - generated scene text into Scene objects."""
        scenes = []
        scene_sections = scene_text.split("Scene")

        for i, section in enumerate(scene_sections[1:], 1):  # Skip first empty section
            if len(section.strip()) < 20:
                continue

            lines = [line.strip() for line in section.split("\\n") if line.strip()]

            # Extract scene details
            location = "INTERIOR"
            time_of_day = "DAY"
            description = "Scene description"

            for line in lines:
                if "location" in line.lower() or "setting" in line.lower():
                    location = line.split(":")[-1].strip() if ":" in line else "INTERIOR"
                elif "time" in line.lower():
                    time_of_day = line.split(":")[-1].strip() if ":" in line else "DAY"
                elif len(line) > 30 and not any(
                    keyword in line.lower()
                    for keyword in ["scene", "location", "time", "character"]
# BRACKET_SURGEON: disabled
#                 ):
                    description = line[:200]  # Use first substantial line as description
                    break

            scene = Scene(
                number=i,
                location=location,
                time_of_day=time_of_day,
                characters=character_names[:2],  # Use first 2 characters
                description=description,
                dialogue=[],
                action=["Action to be developed"],
                duration_estimate=total_duration * 60 // len(scene_sections[1:]),
# BRACKET_SURGEON: disabled
#             )
            scenes.append(scene)

        # Ensure at least 3 scenes
        while len(scenes) < 3:
            scenes.append(
                Scene(
                    number=len(scenes) + 1,
                    location="LOCATION",
                    time_of_day="DAY",
                    characters=(character_names[:1] if character_names else ["CHARACTER"]),
                    description="Scene description",
                    dialogue=[],
                    action=["Action description"],
                    duration_estimate=total_duration * 60 // 3,
# BRACKET_SURGEON: disabled
#                 )
# BRACKET_SURGEON: disabled
#             )

        return scenes

    def write_scene_script(self, scene: Scene, characters: List[Character]) -> Scene:
        """Write full script for a specific scene."""
        logger.info(f"Writing script for scene {scene.number}")

        character_info = "\\n".join([f"{char.name}: {char.description}" for char in characters])

        scene_details = f""""""
Scene {scene.number}: {scene.location} - {scene.time_of_day}
Characters: {', '.join(scene.characters)}
Description: {scene.description}
""""""

        prompt = self.script_templates["script_prompt"].format(
            scene_details=scene_details, characters=character_info
# BRACKET_SURGEON: disabled
#         )

        system_prompt = (
            "You are a professional screenwriter who writes engaging, properly formatted scripts."
# BRACKET_SURGEON: disabled
#         )

        script_text = self.llm.generate(prompt, system_prompt, max_tokens=1500)

        if script_text:
            # Parse script into dialogue and action
            dialogue, action = self._parse_script_text(script_text)
            scene.dialogue = dialogue
            scene.action = action
        else:
            logger.error(f"Failed to generate script for scene {scene.number}")
            scene.dialogue = [{"character": scene.characters[0], "line": "Dialogue to be written"}]
            scene.action = ["Action to be written"]

        return scene

    def _parse_script_text(self, script_text: str) -> Tuple[List[Dict[str, str]], List[str]]:
        """Parse script text into dialogue and action lists."""
        dialogue = []
        action = []

        lines = script_text.split("\\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if line is dialogue (CHARACTER NAME in caps followed by dialogue)
            if line.isupper() and len(line.split()) <= 3:
                # This might be a character name, next line should be dialogue
                continue
            elif ":" in line and len(line.split(":")[0].split()) <= 2:
                # Format: CHARACTER: dialogue
                parts = line.split(":", 1)
                character = parts[0].strip().upper()
                line_text = parts[1].strip()
                dialogue.append({"character": character, "line": line_text})
            elif not line.startswith("(") and len(line) > 10:
                # Likely action line
                action.append(line)

        # Ensure we have some content
        if not dialogue:
            dialogue.append({"character": "CHARACTER", "line": "Dialogue content"})
        if not action:
            action.append("Action description")

        return dialogue, action

    def generate_full_script(
        self,
        topic: str,
        genre: str = "Drama",
        duration: int = 10,
        audience: str = "General",
# BRACKET_SURGEON: disabled
#     ) -> Script:
        """Generate complete script through all stages."""
        logger.info(f"Starting full script generation for: {topic}")

        try:
            # Stage 1: Logline
            logline = self.create_logline(topic, genre, duration, audience)
            time.sleep(1)  # Rate limiting

            # Stage 2: Synopsis
            synopsis = self.create_synopsis(logline, duration)
            time.sleep(1)

            # Stage 3: Characters
            characters = self.develop_characters(synopsis, genre)
            time.sleep(1)

            # Stage 4: Scene Breakdown
            scenes = self.create_scene_breakdown(synopsis, characters, duration)
            time.sleep(1)

            # Stage 5: Write each scene
            for i, scene in enumerate(scenes):
                scenes[i] = self.write_scene_script(scene, characters)
                time.sleep(1)  # Rate limiting between scenes

            # Calculate total duration
            total_duration = sum(scene.duration_estimate for scene in scenes)

            script = Script(
                title=topic.title(),
                logline=logline,
                synopsis=synopsis,
                characters=characters,
                scenes=scenes,
                total_duration=total_duration,
                genre=genre,
                target_audience=audience,
                created_at=datetime.now(),
                version="1.0",
# BRACKET_SURGEON: disabled
#             )

            logger.info(f"Successfully generated script: {script.title}")
            return script

        except Exception as e:
            logger.error(f"Error generating script: {e}")
            raise

    def export_script(self, script: Script, output_path: str, format_type: str = "json") -> bool:
        """Export script to file."""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            if format_type.lower() == "json":
                with open(output_file, "w", encoding="utf - 8") as f:
                    json.dump(asdict(script), f, indent=2, default=str)

            elif format_type.lower() == "txt":
                with open(output_file, "w", encoding="utf - 8") as f:
                    f.write(f"TITLE: {script.title}\\n\\n")
                    f.write(f"LOGLINE: {script.logline}\\n\\n")
                    f.write(f"SYNOPSIS:\\n{script.synopsis}\\n\\n")

                    f.write("CHARACTERS:\\n")
                    for char in script.characters:
                        f.write(f"- {char.name}: {char.description}\\n")
                    f.write("\\n")

                    f.write("SCRIPT:\\n\\n")
                    for scene in script.scenes:
                        f.write(f"SCENE {scene.number} - {scene.location} - {scene.time_of_day}\\n")
                        f.write(f"{scene.description}\\n\\n")

                        for action_line in scene.action:
                            f.write(f"{action_line}\\n")

                        for dialogue in scene.dialogue:
                            f.write(f"\\n{dialogue['character']}\\n{dialogue['line']}\\n")

                        f.write("\\n" + "=" * 50 + "\\n\\n")

            logger.info(f"Script exported to: {output_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to export script: {e}")
            return False

    def get_script_statistics(self, script: Script) -> Dict[str, Any]:
        """Get detailed statistics about the script."""
        total_dialogue_lines = sum(len(scene.dialogue) for scene in script.scenes)
        total_action_lines = sum(len(scene.action) for scene in script.scenes)

        character_dialogue_count = {}
        for scene in script.scenes:
            for dialogue in scene.dialogue:
                char = dialogue["character"]
                character_dialogue_count[char] = character_dialogue_count.get(char, 0) + 1

        return {
            "title": script.title,
            "total_scenes": len(script.scenes),
            "total_characters": len(script.characters),
            "estimated_duration_minutes": script.total_duration // 60,
            "total_dialogue_lines": total_dialogue_lines,
            "total_action_lines": total_action_lines,
            "character_dialogue_distribution": character_dialogue_count,
            "average_scene_duration": (
                script.total_duration // len(script.scenes) if script.scenes else 0
# BRACKET_SURGEON: disabled
#             ),
            "genre": script.genre,
            "target_audience": script.target_audience,
            "created_at": script.created_at.isoformat(),
# BRACKET_SURGEON: disabled
#         }


# Example usage and testing
if __name__ == "__main__":
    # Initialize VidScriptPro
    scriptwriter = VidScriptPro()

    # Test Ollama connection
    if scriptwriter.llm.health_check():
        print("✅ Ollama connection successful")

        # Generate a sample script
        try:
            script = scriptwriter.generate_full_script(
                topic="A day in the life of a coffee shop owner",
                genre="Slice of Life",
                duration=5,
                audience="General",
# BRACKET_SURGEON: disabled
#             )

            # Print statistics
            stats = scriptwriter.get_script_statistics(script)
            print("\\n📊 Script Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")

            # Export script
            scriptwriter.export_script(script, "output/sample_script.json")
            scriptwriter.export_script(script, "output/sample_script.txt", "txt")

        except Exception as e:
            print(f"❌ Error generating script: {e}")
    else:
        print("❌ Ollama server not accessible. Please ensure Ollama is running on localhost:11434")
        print("   You can start Ollama with: ollama serve")
        print("   And pull a model with: ollama pull llama2")