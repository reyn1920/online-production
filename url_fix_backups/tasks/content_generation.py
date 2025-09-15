# tasks / content_generation.py - AI content generation tasks

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import openai
import requests
from celery import Task

from celery_app import celery_app

logger = logging.getLogger(__name__)


class ContentGenerationTask(Task):
    """Base class for content generation tasks with retry logic"""

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3, "countdown": 60}
    retry_backoff = True
    retry_jitter = False

@celery_app.task(base = ContentGenerationTask, bind = True)


def generate_ai_content(
    self, content_type: str, specifications: Dict[str, Any]
) -> Dict[str, Any]:
    """"""
    Generate AI content based on type and specifications

    Args:
        content_type: Type of content (story, design, music, etc.)
        specifications: Content requirements and parameters

    Returns:
        Dict containing generated content and metadata
    """"""
    try:
        logger.info(f"Generating {content_type} content with specs: {specifications}")

        # Route to appropriate generation function
        generators = {
            "children_story": generate_children_story,
                "interior_design": generate_interior_design,
                "brand_identity": generate_brand_identity,
                "meditation_audio": generate_meditation_script,
                "fitness_plan": generate_fitness_plan,
                "stock_music": generate_music_composition,
                "infographic": generate_infographic_content,
                "art_pack": generate_digital_art,
                "product_mockup": generate_product_mockup,
                "saas_boilerplate": generate_saas_code,
# BRACKET_SURGEON: disabled
#                 }

        generator_func = generators.get(content_type)
        if not generator_func:
            raise ValueError(f"Unknown content type: {content_type}")

        result = generator_func(specifications)

        logger.info(f"Successfully generated {content_type} content")
        return {
            "status": "success",
                "content_type": content_type,
                "content": result,
                "generated_at": datetime.utcnow().isoformat(),
                "task_id": self.request.id,
# BRACKET_SURGEON: disabled
#                 }

    except Exception as e:
        logger.error(f"Content generation failed: {str(e)}")
        raise self.retry(exc = e)


def generate_children_story(specs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate personalized children's storybook"""'

    # OpenAI API call for story generation
    openai.api_key = os.getenv("OPENAI_API_KEY")

    prompt = f""""""
    Create a personalized children's story with these specifications:'
    - Child's name: {specs.get('child_name', 'Alex')}'
    - Age: {specs.get('age', 5)}
    - Theme: {specs.get('theme', 'adventure')}
    - Setting: {specs.get('setting', 'magical forest')}
    - Moral lesson: {specs.get('moral', 'friendship')}
    - Length: {specs.get('length', 'short')} story

    Include vivid descriptions for illustrations and make it age - appropriate.
    """"""

    response = openai.ChatCompletion.create(
        model="gpt - 4",
            messages=[
            {
                "role": "system",
                    "content": "You are a creative children's book author who writes engaging, educational stories.",'
# BRACKET_SURGEON: disabled
#                     },
                {"role": "user", "content": prompt},
# BRACKET_SURGEON: disabled
#                 ],
            max_tokens = 2000,
            temperature = 0.8,
# BRACKET_SURGEON: disabled
#             )

    story_text = response.choices[0].message.content

    return {
        "story_text": story_text,
            "title": f"{specs.get('child_name', 'Alex')}'s {specs.get('theme', 'Adventure')}",'
            "specifications": specs,
            "word_count": len(story_text.split()),
            "illustration_prompts": extract_illustration_prompts(story_text),
# BRACKET_SURGEON: disabled
#             }


def generate_interior_design(specs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate AI interior design recommendations"""

    openai.api_key = os.getenv("OPENAI_API_KEY")

    prompt = f""""""
    Create a comprehensive interior design plan:
    - Room type: {specs.get('room_type', 'living room')}
    - Style: {specs.get('style', 'modern')}
    - Budget: {specs.get('budget', 'medium')}
    - Color preferences: {specs.get('colors', 'neutral')}
    - Room size: {specs.get('size', 'medium')}
    - Special requirements: {specs.get('requirements', 'none')}

    Provide detailed recommendations for furniture, colors, lighting, and decor.
    """"""

    response = openai.ChatCompletion.create(
        model="gpt - 4",
            messages=[
            {
                "role": "system",
                    "content": "You are a professional interior designer with expertise in various styles \"
#     and budgets.",
# BRACKET_SURGEON: disabled
#                     },
                {"role": "user", "content": prompt},
# BRACKET_SURGEON: disabled
#                 ],
            max_tokens = 1500,
            temperature = 0.7,
# BRACKET_SURGEON: disabled
#             )

    design_plan = response.choices[0].message.content

    return {
        "design_plan": design_plan,
            "room_type": specs.get("room_type"),
            "style": specs.get("style"),
            "budget_estimate": calculate_budget_estimate(specs),
            "shopping_list": extract_shopping_items(design_plan),
            "mood_board_elements": extract_mood_board_elements(design_plan),
# BRACKET_SURGEON: disabled
#             }


def generate_brand_identity(specs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate complete brand identity kit"""

    openai.api_key = os.getenv("OPENAI_API_KEY")

    prompt = f""""""
    Create a comprehensive brand identity for:
    - Business name: {specs.get('business_name', 'New Business')}
    - Industry: {specs.get('industry', 'technology')}
    - Target audience: {specs.get('target_audience', 'young professionals')}
    - Brand personality: {specs.get('personality', 'innovative and friendly')}
    - Values: {specs.get('values', 'quality and innovation')}

    Include logo concepts, color palette, typography, voice guidelines, \
#     and marketing materials.
    """"""

    response = openai.ChatCompletion.create(
        model="gpt - 4",
            messages=[
            {
                "role": "system",
                    "content": "You are a brand strategist \"
#     and designer who creates cohesive brand identities.",
# BRACKET_SURGEON: disabled
#                     },
                {"role": "user", "content": prompt},
# BRACKET_SURGEON: disabled
#                 ],
            max_tokens = 2000,
            temperature = 0.7,
# BRACKET_SURGEON: disabled
#             )

    brand_guide = response.choices[0].message.content

    return {
        "brand_guide": brand_guide,
            "business_name": specs.get("business_name"),
            "logo_concepts": extract_logo_concepts(brand_guide),
            "color_palette": extract_color_palette(brand_guide),
            "typography": extract_typography(brand_guide),
            "voice_guidelines": extract_voice_guidelines(brand_guide),
# BRACKET_SURGEON: disabled
#             }


def generate_meditation_script(specs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate personalized meditation audio script"""

    openai.api_key = os.getenv("OPENAI_API_KEY")

    prompt = f""""""
    Create a meditation script with these parameters:
    - Duration: {specs.get('duration', 10)} minutes
    - Focus: {specs.get('focus', 'relaxation')}
    - Voice style: {specs.get('voice_style', 'calm and soothing')}
    - Background: {specs.get('background', 'nature sounds')}
    - Experience level: {specs.get('level', 'beginner')}

    Include timing cues and breathing instructions.
    """"""

    response = openai.ChatCompletion.create(
        model="gpt - 4",
            messages=[
            {
                "role": "system",
                    "content": "You are a meditation instructor who creates guided meditation scripts.",
# BRACKET_SURGEON: disabled
#                     },
                {"role": "user", "content": prompt},
# BRACKET_SURGEON: disabled
#                 ],
            max_tokens = 1500,
            temperature = 0.6,
# BRACKET_SURGEON: disabled
#             )

    script = response.choices[0].message.content

    return {
        "script": script,
            "duration": specs.get("duration"),
            "focus": specs.get("focus"),
            "timing_cues": extract_timing_cues(script),
            "audio_elements": extract_audio_elements(script),
# BRACKET_SURGEON: disabled
#             }


def generate_fitness_plan(specs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate personalized fitness plan"""

    openai.api_key = os.getenv("OPENAI_API_KEY")

    prompt = f""""""
    Create a personalized fitness plan:
    - Fitness level: {specs.get('fitness_level', 'beginner')}
    - Goals: {specs.get('goals', 'general fitness')}
    - Available time: {specs.get('time_available', '30 minutes')}
    - Equipment: {specs.get('equipment', 'bodyweight only')}
    - Preferences: {specs.get('preferences', 'varied workouts')}
    - Duration: {specs.get('plan_duration', '4 weeks')}

    Include detailed workout schedules, exercise descriptions, and progression plans.
    """"""

    response = openai.ChatCompletion.create(
        model="gpt - 4",
            messages=[
            {
                "role": "system",
                    "content": "You are a certified fitness trainer who creates personalized workout plans.",
# BRACKET_SURGEON: disabled
#                     },
                {"role": "user", "content": prompt},
# BRACKET_SURGEON: disabled
#                 ],
            max_tokens = 2000,
            temperature = 0.7,
# BRACKET_SURGEON: disabled
#             )

    fitness_plan = response.choices[0].message.content

    return {
        "fitness_plan": fitness_plan,
            "workout_schedule": extract_workout_schedule(fitness_plan),
            "exercise_library": extract_exercises(fitness_plan),
            "progression_plan": extract_progression(fitness_plan),
            "nutrition_tips": extract_nutrition_tips(fitness_plan),
# BRACKET_SURGEON: disabled
#             }


def generate_music_composition(specs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate AI music composition metadata and structure"""

    # Note: This would integrate with AI music generation APIs like AIVA, Amper, \
#     or Mubert
    # For now, we'll generate the composition structure and metadata

    composition_data = {
        "title": f"{specs.get('mood', 'Ambient')} {specs.get('genre', 'Electronic')} Track",
            "genre": specs.get("genre", "electronic"),
            "mood": specs.get("mood", "calm"),
            "duration": specs.get("duration", 180),  # seconds
        "bpm": specs.get("bpm", 120),
            "key": specs.get("key", "C major"),
            "instruments": specs.get("instruments", ["piano", "strings", "ambient pad"]),
            "structure": generate_music_structure(specs),
            "metadata": {
            "created_at": datetime.utcnow().isoformat(),
                "license": "royalty - free",
                "usage_rights": "commercial use allowed",
# BRACKET_SURGEON: disabled
#                 },
# BRACKET_SURGEON: disabled
#             }

    return composition_data


def generate_infographic_content(specs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate data - driven infographic content"""

    openai.api_key = os.getenv("OPENAI_API_KEY")

    prompt = f""""""
    Create content for a data - driven infographic:
    - Topic: {specs.get('topic', 'technology trends')}
    - Target audience: {specs.get('audience', 'business professionals')}
    - Data sources: {specs.get('data_sources', 'industry reports')}
    - Style: {specs.get('style', 'modern and clean')}
    - Key message: {specs.get('message', 'inform and educate')}

    Include statistics, key points, visual elements, and data visualizations.
    """"""

    response = openai.ChatCompletion.create(
        model="gpt - 4",
            messages=[
            {
                "role": "system",
                    "content": "You are a data visualization expert who creates compelling infographic content.",
# BRACKET_SURGEON: disabled
#                     },
                {"role": "user", "content": prompt},
# BRACKET_SURGEON: disabled
#                 ],
            max_tokens = 1500,
            temperature = 0.7,
# BRACKET_SURGEON: disabled
#             )

    content = response.choices[0].message.content

    return {
        "content": content,
            "topic": specs.get("topic"),
            "statistics": extract_statistics(content),
            "visual_elements": extract_visual_elements(content),
            "layout_suggestions": extract_layout_suggestions(content),
# BRACKET_SURGEON: disabled
#             }


def generate_digital_art(specs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate digital art pack concepts"""

    art_concepts = []
    theme = specs.get("theme", "abstract")
    style = specs.get("style", "modern")
    count = specs.get("count", 5)

    for i in range(count):
        concept = {
            "title": f"{theme.title()} Art {i + 1}",
                "description": f"{style.title()} {theme} artwork with unique composition",
                "style": style,
                "theme": theme,
                "color_scheme": generate_color_scheme(),
                "composition": generate_composition_notes(),
                "dimensions": specs.get("dimensions", "1920x1080"),
                "format": specs.get("format", "PNG"),
# BRACKET_SURGEON: disabled
#                 }
        art_concepts.append(concept)

    return {
        "art_concepts": art_concepts,
            "theme": theme,
            "style": style,
            "total_pieces": count,
            "package_info": {
            "license": "commercial use",
                "formats": ["PNG", "JPG", "SVG"],
                "resolutions": ["HD", "4K", "Print - ready"],
# BRACKET_SURGEON: disabled
#                 },
# BRACKET_SURGEON: disabled
#             }


def generate_product_mockup(specs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate e - commerce product mockup specifications"""

    product_type = specs.get("product_type", "t - shirt")
    style = specs.get("style", "minimalist")

    mockup_data = {
        "product_type": product_type,
            "style": style,
            "views": ["front", "back", "side", "detail"],
            "backgrounds": ["white", "lifestyle", "transparent"],
            "lighting": specs.get("lighting", "natural"),
            "resolution": specs.get("resolution", "4K"),
            "file_formats": ["PSD", "PNG", "JPG"],
            "smart_objects": True,
            "customization_options": {
            "colors": True,
                "textures": True,
                "branding": True,
                "text": True,
# BRACKET_SURGEON: disabled
#                 },
# BRACKET_SURGEON: disabled
#             }

    return mockup_data


def generate_saas_code(specs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate SaaS boilerplate code structure"""

    tech_stack = specs.get("tech_stack", "react - node")
    features = specs.get("features", ["auth", "dashboard", "api"])

    code_structure = {
        "tech_stack": tech_stack,
            "features": features,
            "file_structure": generate_file_structure(tech_stack, features),
            "dependencies": generate_dependencies(tech_stack),
            "configuration": generate_config_files(tech_stack),
            "documentation": generate_documentation_outline(features),
            "deployment": generate_deployment_config(tech_stack),
# BRACKET_SURGEON: disabled
#             }

    return code_structure

# Helper functions


def extract_illustration_prompts(text: str) -> List[str]:
    """Extract illustration prompts from story text"""
    # Simple implementation - would use NLP in production
    sentences = text.split(".")
    return [s.strip() for s in sentences if len(s.strip()) > 20][:5]


def calculate_budget_estimate(specs: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate budget estimate for interior design"""
    base_costs = {"low": 1000, "medium": 5000, "high": 15000}

    budget_level = specs.get("budget", "medium")
    return {
        "estimated_total": base_costs.get(budget_level, 5000),
            "breakdown": {
            "furniture": 0.6,
                "decor": 0.2,
                "lighting": 0.1,
                "miscellaneous": 0.1,
# BRACKET_SURGEON: disabled
#                 },
# BRACKET_SURGEON: disabled
#             }


def extract_shopping_items(design_plan: str) -> List[str]:
    """Extract shopping items from design plan"""
    # Simple keyword extraction - would use NLP in production
    items = []
    keywords = ["sofa", "chair", "table", "lamp", "rug", "curtains", "artwork"]
    for keyword in keywords:
        if keyword in design_plan.lower():
            items.append(keyword)
    return items


def extract_mood_board_elements(design_plan: str) -> List[str]:
    """Extract mood board elements"""
    return [
        "color swatches",
            "texture samples",
            "furniture images",
            "lighting examples",
# BRACKET_SURGEON: disabled
#             ]


def extract_logo_concepts(brand_guide: str) -> List[Dict[str, str]]:
    """Extract logo concepts from brand guide"""
    return [
        {"type": "wordmark", "description": "Text - based logo"},
            {"type": "symbol", "description": "Icon - based logo"},
            {"type": "combination", "description": "Text and symbol combined"},
# BRACKET_SURGEON: disabled
#             ]


def extract_color_palette(brand_guide: str) -> Dict[str, str]:
    """Extract color palette"""
    return {
        "primary": "#2563eb","
            "secondary": "#64748b","
            "accent": "#f59e0b","
            "neutral": "#f8fafc","
# BRACKET_SURGEON: disabled
#             }


def extract_typography(brand_guide: str) -> Dict[str, str]:
    """Extract typography recommendations"""
    return {"heading": "Inter", "body": "Open Sans", "accent": "Playfair Display"}


def extract_voice_guidelines(brand_guide: str) -> Dict[str, str]:
    """Extract voice and tone guidelines"""
    return {
        "tone": "Professional yet approachable",
            "voice": "Confident and helpful",
            "style": "Clear and concise",
# BRACKET_SURGEON: disabled
#             }


def extract_timing_cues(script: str) -> List[Dict[str, Any]]:
    """Extract timing cues from meditation script"""
    return [
        {"time": "0:00", "action": "Begin with deep breathing"},
            {"time": "2:00", "action": "Body scan meditation"},
            {"time": "5:00", "action": "Mindfulness practice"},
            {"time": "8:00", "action": "Closing and return to awareness"},
# BRACKET_SURGEON: disabled
#             ]


def extract_audio_elements(script: str) -> List[str]:
    """Extract audio elements needed"""
    return ["nature sounds", "soft music", "voice recording", "silence periods"]


def extract_workout_schedule(fitness_plan: str) -> Dict[str, List[str]]:
    """Extract workout schedule"""
    return {
        "monday": ["Upper body strength", "30 minutes"],
            "tuesday": ["Cardio", "25 minutes"],
            "wednesday": ["Lower body strength", "30 minutes"],
            "thursday": ["Active recovery", "20 minutes"],
            "friday": ["Full body circuit", "35 minutes"],
            "saturday": ["Flexibility / Yoga", "30 minutes"],
            "sunday": ["Rest day", "0 minutes"],
# BRACKET_SURGEON: disabled
#             }


def extract_exercises(fitness_plan: str) -> List[Dict[str, Any]]:
    """Extract exercise library"""
    return [
        {"name": "Push - ups", "type": "strength", "muscle_groups": ["chest", "arms"]},
            {"name": "Squats", "type": "strength", "muscle_groups": ["legs", "glutes"]},
            {"name": "Plank", "type": "core", "muscle_groups": ["core", "shoulders"]},
# BRACKET_SURGEON: disabled
#             ]


def extract_progression(fitness_plan: str) -> Dict[str, str]:
    """Extract progression plan"""
    return {
        "week_1": "Foundation building",
            "week_2": "Intensity increase",
            "week_3": "Skill development",
            "week_4": "Performance optimization",
# BRACKET_SURGEON: disabled
#             }


def extract_nutrition_tips(fitness_plan: str) -> List[str]:
    """Extract nutrition tips"""
    return [
        "Stay hydrated throughout the day",
            "Eat protein within 30 minutes post - workout",
            "Include complex carbohydrates for energy",
            "Focus on whole, unprocessed foods",
# BRACKET_SURGEON: disabled
#             ]


def generate_music_structure(specs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate music composition structure"""
    return {
        "intro": {"duration": 15, "description": "Atmospheric opening"},
            "verse_1": {"duration": 30, "description": "Main melody introduction"},
            "chorus": {"duration": 30, "description": "Energetic hook section"},
            "verse_2": {"duration": 30, "description": "Melody development"},
            "bridge": {"duration": 20, "description": "Contrasting section"},
            "outro": {"duration": 25, "description": "Gradual fade"},
# BRACKET_SURGEON: disabled
#             }


def extract_statistics(content: str) -> List[Dict[str, Any]]:
    """Extract statistics from infographic content"""
    return [
        {"value": "75%", "description": "Market growth rate"},
            {"value": "2.5x", "description": "Performance improvement"},
            {"value": "$1.2B", "description": "Market size"},
# BRACKET_SURGEON: disabled
#             ]


def extract_visual_elements(content: str) -> List[str]:
    """Extract visual elements for infographic"""
    return ["charts", "icons", "illustrations", "data visualizations"]


def extract_layout_suggestions(content: str) -> List[str]:
    """Extract layout suggestions"""
    return ["header with title", "three - column data section", "footer with sources"]


def generate_color_scheme() -> Dict[str, str]:
    """Generate color scheme for digital art"""
    schemes = [
        {"primary": "#ff6b6b", "secondary": "#4ecdc4", "accent": "#45b7d1"},"
            {"primary": "#96ceb4", "secondary": "#ffeaa7", "accent": "#dda0dd"},"
            {"primary": "#74b9ff", "secondary": "#fd79a8", "accent": "#fdcb6e"},"
# BRACKET_SURGEON: disabled
#             ]

    import random

    return random.choice(schemes)


def generate_composition_notes() -> str:
    """Generate composition notes for digital art"""
    compositions = [
        "Rule of thirds with dynamic focal point",
            "Symmetrical balance with central emphasis",
            "Asymmetrical composition with visual flow",
            "Radial composition with outward movement",
# BRACKET_SURGEON: disabled
#             ]

    import random

    return random.choice(compositions)


def generate_file_structure(tech_stack: str, features: List[str]) -> Dict[str, Any]:
    """Generate file structure for SaaS boilerplate"""
    return {
        "frontend": {
            "src": ["components", "pages", "hooks", "utils", "styles"],
                "public": ["index.html", "favicon.ico"],
# BRACKET_SURGEON: disabled
#                 },
            "backend": {
            "src": ["routes", "models", "middleware", "utils", "config"],
                "tests": ["unit", "integration"],
# BRACKET_SURGEON: disabled
#                 },
            "shared": ["types", "constants", "validators"],
# BRACKET_SURGEON: disabled
#             }


def generate_dependencies(tech_stack: str) -> Dict[str, List[str]]:
    """Generate dependencies for tech stack"""
    return {
        "frontend": ["react", "typescript", "tailwindcss", "axios"],
            "backend": ["express", "typescript", "prisma", "bcrypt", "jsonwebtoken"],
            "dev": ["jest", "eslint", "prettier", "nodemon"],
# BRACKET_SURGEON: disabled
#             }


def generate_config_files(tech_stack: str) -> List[str]:
    """Generate configuration files needed"""
    return [
        "package.json",
            "tsconfig.json",
            ".env.example",
            "docker - compose.yml",
            ".gitignore",
            "README.md",
# BRACKET_SURGEON: disabled
#             ]


def generate_documentation_outline(features: List[str]) -> Dict[str, List[str]]:
    """Generate documentation outline"""
    return {
        "setup": ["Installation", "Configuration", "Environment Setup"],
            "api": ["Authentication", "Endpoints", "Error Handling"],
            "deployment": ["Docker", "CI / CD", "Environment Variables"],
# BRACKET_SURGEON: disabled
#             }


def generate_deployment_config(tech_stack: str) -> Dict[str, Any]:
    """Generate deployment configuration"""
    return {
        "docker": True,
            "platforms": ["netlify", "vercel", "heroku"],
            "ci_cd": "github - actions",
            "database": "postgresql",
            "caching": "redis",
# BRACKET_SURGEON: disabled
#             }