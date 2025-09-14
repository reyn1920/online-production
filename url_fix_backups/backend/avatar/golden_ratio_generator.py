#!/usr / bin / env python3
"""
Golden Ratio Avatar Generator

Generates aesthetically pleasing avatars using golden ratio proportions
and mathematical design principles for channels without existing avatars.
"""

import colorsys
import json
import logging
import math
import os
import random
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AvatarStyle(Enum):
    """Avatar style options."""

    GEOMETRIC = "geometric"
    ORGANIC = "organic"
    MINIMALIST = "minimalist"
    PROFESSIONAL = "professional"
    CREATIVE = "creative"
    TECH = "tech"


class ColorScheme(Enum):
    """Color scheme options."""

    MONOCHROMATIC = "monochromatic"
    COMPLEMENTARY = "complementary"
    TRIADIC = "triadic"
    ANALOGOUS = "analogous"
    SPLIT_COMPLEMENTARY = "split_complementary"


@dataclass
class GoldenRatioConfig:
    """Configuration for golden ratio avatar generation."""

    width: int = 512
    height: int = 512
    style: AvatarStyle = AvatarStyle.PROFESSIONAL
    color_scheme: ColorScheme = ColorScheme.COMPLEMENTARY
    base_hue: float = 0.6  # Blue - ish by default
    complexity: float = 0.7  # 0.0 to 1.0
    symmetry: bool = True
    include_text: bool = False
    channel_name: Optional[str] = None
    seed: Optional[int] = None


class GoldenRatioAvatarGenerator:
    """Generates avatars using golden ratio proportions."""

    # Golden ratio constant
    PHI = (1 + math.sqrt(5)) / 2  # ≈ 1.618

    def __init__(self, config: Optional[GoldenRatioConfig] = None):
        self.config = config or GoldenRatioConfig()
        if self.config.seed:
            random.seed(self.config.seed)
            np.random.seed(self.config.seed)

        # Golden ratio derived proportions
        self.proportions = {
            "major_section": 1 / self.PHI,  # ≈ 0.618
            "minor_section": 1 - (1 / self.PHI),  # ≈ 0.382
            "spiral_ratio": self.PHI,
            "rectangle_ratio": self.PHI,
        }

        logger.info(f"Initialized Golden Ratio Avatar Generator with PHI={self.PHI:.3f}")

    def generate_avatar(self, channel_name: str, **kwargs) -> Image.Image:
        """Generate a golden ratio avatar for a channel."""
        # Update config with any provided parameters
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        self.config.channel_name = channel_name

        logger.info(f"Generating golden ratio avatar for channel: {channel_name}")

        # Create base image
        image = Image.new("RGBA", (self.config.width, self.config.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Generate color palette
        colors = self._generate_color_palette()

        # Apply style - specific generation
        if self.config.style == AvatarStyle.GEOMETRIC:
            image = self._generate_geometric_avatar(image, draw, colors)
        elif self.config.style == AvatarStyle.ORGANIC:
            image = self._generate_organic_avatar(image, draw, colors)
        elif self.config.style == AvatarStyle.MINIMALIST:
            image = self._generate_minimalist_avatar(image, draw, colors)
        elif self.config.style == AvatarStyle.PROFESSIONAL:
            image = self._generate_professional_avatar(image, draw, colors)
        elif self.config.style == AvatarStyle.CREATIVE:
            image = self._generate_creative_avatar(image, draw, colors)
        elif self.config.style == AvatarStyle.TECH:
            image = self._generate_tech_avatar(image, draw, colors)

        # Add channel name if requested
        if self.config.include_text and self.config.channel_name:
            image = self._add_channel_text(image, self.config.channel_name, colors)

        # Apply post - processing
        image = self._apply_post_processing(image)

        logger.info(f"Successfully generated avatar for {channel_name}")
        return image

    def _generate_color_palette(self) -> List[Tuple[int, int, int, int]]:
        """Generate a color palette based on golden ratio and color theory."""
        base_hue = self.config.base_hue
        colors = []

        if self.config.color_scheme == ColorScheme.MONOCHROMATIC:
            # Variations of the same hue
            for i in range(5):
                saturation = 0.3 + (i * 0.15)
                lightness = 0.2 + (i * 0.15)
                rgb = colorsys.hls_to_rgb(base_hue, lightness, saturation)
                colors.append(tuple(int(c * 255) for c in rgb) + (255,))

        elif self.config.color_scheme == ColorScheme.COMPLEMENTARY:
            # Base color and its complement
            complement_hue = (base_hue + 0.5) % 1.0
            for hue in [base_hue, complement_hue]:
                for lightness in [0.3, 0.5, 0.7]:
                    rgb = colorsys.hls_to_rgb(hue, lightness, 0.8)
                    colors.append(tuple(int(c * 255) for c in rgb) + (255,))

        elif self.config.color_scheme == ColorScheme.TRIADIC:
            # Three colors equally spaced on color wheel
            for i in range(3):
                hue = (base_hue + i * (1 / 3)) % 1.0
                rgb = colorsys.hls_to_rgb(hue, 0.5, 0.8)
                colors.append(tuple(int(c * 255) for c in rgb) + (255,))

        elif self.config.color_scheme == ColorScheme.ANALOGOUS:
            # Adjacent colors on color wheel
            for i in range(-2, 3):
                hue = (base_hue + i * 0.1) % 1.0
                rgb = colorsys.hls_to_rgb(hue, 0.5, 0.8)
                colors.append(tuple(int(c * 255) for c in rgb) + (255,))

        elif self.config.color_scheme == ColorScheme.SPLIT_COMPLEMENTARY:
            # Base color and two colors adjacent to its complement
            complement = (base_hue + 0.5) % 1.0
            hues = [base_hue, (complement - 0.1) % 1.0, (complement + 0.1) % 1.0]
            for hue in hues:
                rgb = colorsys.hls_to_rgb(hue, 0.5, 0.8)
                colors.append(tuple(int(c * 255) for c in rgb) + (255,))

        return colors[:6]  # Limit to 6 colors

    def _generate_geometric_avatar(
        self, image: Image.Image, draw: ImageDraw.Draw, colors: List
    ) -> Image.Image:
        """Generate geometric avatar using golden ratio proportions."""
        w, h = image.size
        center_x, center_y = w // 2, h // 2

        # Golden ratio rectangles
        major_w = int(w * self.proportions["major_section"])
        minor_w = w - major_w
        major_h = int(h * self.proportions["major_section"])
        minor_h = h - major_h

        # Draw nested golden rectangles
        rectangles = [
            (0, 0, major_w, major_h),
            (major_w, 0, w, minor_h),
            (major_w, minor_h, w, h),
            (0, major_h, minor_w, h),
        ]

        for i, rect in enumerate(rectangles):
            color = colors[i % len(colors)]
            draw.rectangle(rect, fill=color)

        # Add golden spiral elements
        self._draw_golden_spiral(draw, center_x, center_y, min(w, h) // 4, colors[0])

        return image

    def _generate_organic_avatar(
        self, image: Image.Image, draw: ImageDraw.Draw, colors: List
    ) -> Image.Image:
        """Generate organic avatar with natural golden ratio curves."""
        w, h = image.size
        center_x, center_y = w // 2, h // 2

        # Create organic shapes based on golden ratio
        for i in range(int(5 * self.config.complexity)):
            # Golden ratio based positioning
            angle = (i * self.PHI * 137.5) % 360  # Golden angle
            radius = (i + 1) * (min(w, h) / 10) * self.proportions["major_section"]

            x = center_x + int(radius * math.cos(math.radians(angle)))
            y = center_y + int(radius * math.sin(math.radians(angle)))

            # Draw organic circles with golden ratio sizing
            circle_radius = int((i + 1) * 8 * self.proportions["minor_section"])
            color = colors[i % len(colors)]

            draw.ellipse(
                (
                    x - circle_radius,
                    y - circle_radius,
                    x + circle_radius,
                    y + circle_radius,
                ),
                fill=color,
            )

        return image

    def _generate_minimalist_avatar(
        self, image: Image.Image, draw: ImageDraw.Draw, colors: List
    ) -> Image.Image:
        """Generate minimalist avatar with clean golden ratio proportions."""
        w, h = image.size

        # Simple golden ratio division
        division_x = int(w * self.proportions["major_section"])
        division_y = int(h * self.proportions["major_section"])

        # Draw clean sections
        draw.rectangle((0, 0, division_x, h), fill=colors[0])
        draw.rectangle((division_x, 0, w, division_y), fill=colors[1])
        draw.rectangle((division_x, division_y, w, h), fill=colors[2])

        # Add subtle accent
        accent_size = int(min(w, h) * 0.1)
        draw.ellipse(
            (
                division_x - accent_size,
                division_y - accent_size,
                division_x + accent_size,
                division_y + accent_size,
            ),
            fill=colors[3],
        )

        return image

    def _generate_professional_avatar(
        self, image: Image.Image, draw: ImageDraw.Draw, colors: List
    ) -> Image.Image:
        """Generate professional avatar suitable for business channels."""
        w, h = image.size
        center_x, center_y = w // 2, h // 2

        # Professional background gradient effect
        for y in range(h):
            ratio = y / h
            color_index = int(ratio * (len(colors) - 1))
            color = colors[color_index]
            draw.line([(0, y), (w, y)], fill=color)

        # Golden ratio based professional elements
        # Main focal circle
        main_radius = int(min(w, h) * self.proportions["major_section"] / 2)
        draw.ellipse(
            (
                center_x - main_radius,
                center_y - main_radius,
                center_x + main_radius,
                center_y + main_radius,
            ),
            fill=colors[-1],
            outline=colors[0],
            width=3,
        )

        # Accent elements at golden ratio positions
        accent_positions = [
            (
                int(w * self.proportions["major_section"]),
                int(h * self.proportions["minor_section"]),
            ),
            (
                int(w * self.proportions["minor_section"]),
                int(h * self.proportions["major_section"]),
            ),
        ]

        for x, y in accent_positions:
            accent_radius = int(main_radius * self.proportions["minor_section"])
            draw.ellipse(
                (
                    x - accent_radius,
                    y - accent_radius,
                    x + accent_radius,
                    y + accent_radius,
                ),
                fill=colors[1],
            )

        return image

    def _generate_creative_avatar(
        self, image: Image.Image, draw: ImageDraw.Draw, colors: List
    ) -> Image.Image:
        """Generate creative avatar with artistic golden ratio elements."""
        w, h = image.size
        center_x, center_y = w // 2, h // 2

        # Creative spiral pattern
        spiral_points = self._calculate_golden_spiral_points(center_x, center_y, min(w, h) // 6, 50)

        # Draw creative elements along spiral
        for i, (x, y) in enumerate(spiral_points[::3]):  # Every 3rd point
            size = int((i + 1) * 3 * self.config.complexity)
            color = colors[i % len(colors)]

            # Alternate between circles and squares
            if i % 2 == 0:
                draw.ellipse((x - size, y - size, x + size, y + size), fill=color)
            else:
                draw.rectangle((x - size, y - size, x + size, y + size), fill=color)

        # Add creative overlays
        overlay_image = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay_image)

        # Golden ratio based creative lines
        for i in range(int(10 * self.config.complexity)):
            angle = i * 23  # Prime number for interesting patterns
            length = (i + 1) * 20

            x1 = center_x + int(length * math.cos(math.radians(angle)))
            y1 = center_y + int(length * math.sin(math.radians(angle)))
            x2 = center_x + int(length * self.PHI * math.cos(math.radians(angle + 90)))
            y2 = center_y + int(length * self.PHI * math.sin(math.radians(angle + 90)))

            overlay_draw.line([(x1, y1), (x2, y2)], fill=colors[i % len(colors)], width=2)

        # Blend overlay
        image = Image.alpha_composite(image, overlay_image)

        return image

    def _generate_tech_avatar(
        self, image: Image.Image, draw: ImageDraw.Draw, colors: List
    ) -> Image.Image:
        """Generate tech - style avatar with digital golden ratio patterns."""
        w, h = image.size

        # Tech grid based on golden ratio
        grid_size_x = int(w / (self.PHI * 8))
        grid_size_y = int(h / (self.PHI * 8))

        # Draw tech grid
        for x in range(0, w, grid_size_x):
            for y in range(0, h, grid_size_y):
                if random.random() < self.config.complexity:
                    color = colors[random.randint(0, len(colors) - 1)]
                    draw.rectangle((x, y, x + grid_size_x, y + grid_size_y), fill=color)

        # Add tech circuit patterns
        center_x, center_y = w // 2, h // 2

        # Golden ratio based circuit lines
        for i in range(int(8 * self.config.complexity)):
            angle = i * (360 / self.PHI)
            radius1 = (i + 1) * 15
            radius2 = radius1 * self.PHI

            x1 = center_x + int(radius1 * math.cos(math.radians(angle)))
            y1 = center_y + int(radius1 * math.sin(math.radians(angle)))
            x2 = center_x + int(radius2 * math.cos(math.radians(angle)))
            y2 = center_y + int(radius2 * math.sin(math.radians(angle)))

            draw.line([(x1, y1), (x2, y2)], fill=colors[0], width=2)

            # Add connection nodes
            node_size = 3
            draw.ellipse(
                (x1 - node_size, y1 - node_size, x1 + node_size, y1 + node_size),
                fill=colors[1],
            )
            draw.ellipse(
                (x2 - node_size, y2 - node_size, x2 + node_size, y2 + node_size),
                fill=colors[1],
            )

        return image

    def _draw_golden_spiral(
        self,
        draw: ImageDraw.Draw,
        center_x: int,
        center_y: int,
        initial_radius: int,
        color: Tuple[int, int, int, int],
    ):
        """Draw a golden spiral."""
        points = self._calculate_golden_spiral_points(center_x, center_y, initial_radius, 30)

        # Draw spiral as connected lines
        for i in range(len(points) - 1):
            draw.line([points[i], points[i + 1]], fill=color, width=2)

    def _calculate_golden_spiral_points(
        self, center_x: int, center_y: int, initial_radius: int, num_points: int
    ) -> List[Tuple[int, int]]:
        """Calculate points along a golden spiral."""
        points = []

        for i in range(num_points):
            # Golden spiral formula
            angle = i * (2 * math.pi / self.PHI)
            radius = initial_radius * (self.PHI ** (angle / (2 * math.pi)))

            x = center_x + int(radius * math.cos(angle))
            y = center_y + int(radius * math.sin(angle))

            points.append((x, y))

        return points

    def _add_channel_text(
        self,
        image: Image.Image,
        channel_name: str,
        colors: List[Tuple[int, int, int, int]],
    ) -> Image.Image:
        """Add channel name text using golden ratio positioning."""
        draw = ImageDraw.Draw(image)
        w, h = image.size

        # Try to load a font, fall back to default if not available
        try:
            font_size = int(min(w, h) * 0.08)
            font = ImageFont.truetype("/System / Library / Fonts / Arial.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

        # Position text at golden ratio point
        text_x = int(w * self.proportions["minor_section"])
        text_y = int(h * self.proportions["major_section"])

        # Add text with outline for visibility
        outline_color = (0, 0, 0, 255)
        text_color = colors[0] if colors else (255, 255, 255, 255)

        # Draw outline
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    draw.text(
                        (text_x + dx, text_y + dy),
                        channel_name,
                        font=font,
                        fill=outline_color,
                    )

        # Draw main text
        draw.text((text_x, text_y), channel_name, font=font, fill=text_color)

        return image

    def _apply_post_processing(self, image: Image.Image) -> Image.Image:
        """Apply post - processing effects."""
        # Subtle blur for smoothing
        if self.config.complexity > 0.5:
            image = image.filter(ImageFilter.GaussianBlur(radius=0.5))

        # Enhance edges
        if self.config.style in [AvatarStyle.TECH, AvatarStyle.GEOMETRIC]:
            image = image.filter(ImageFilter.EDGE_ENHANCE_MORE)

        return image

    def save_avatar(self, image: Image.Image, filepath: str) -> bool:
        """Save avatar to file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Save as PNG with transparency
            image.save(filepath, "PNG", optimize=True)
            logger.info(f"Avatar saved to: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save avatar: {e}")
            return False

    def generate_avatar_variations(self, channel_name: str, count: int = 3) -> List[Image.Image]:
        """Generate multiple avatar variations for selection."""
        variations = []

        styles = list(AvatarStyle)
        color_schemes = list(ColorScheme)

        for i in range(count):
            # Vary parameters for each variation
            config = GoldenRatioConfig(
                style=styles[i % len(styles)],
                color_scheme=color_schemes[i % len(color_schemes)],
                base_hue=random.random(),
                complexity=0.3 + (i * 0.2),
                seed=i,
            )

            generator = GoldenRatioAvatarGenerator(config)
            avatar = generator.generate_avatar(channel_name)
            variations.append(avatar)

        return variations


# Utility functions for integration


def create_channel_avatar(
    channel_name: str, style: str = "professional", output_dir: str = "assets / avatars"
) -> str:
    """Create a golden ratio avatar for a channel."""
    try:
        style_enum = AvatarStyle(style.lower())
    except ValueError:
        style_enum = AvatarStyle.PROFESSIONAL

    config = GoldenRatioConfig(style=style_enum, include_text=True, channel_name=channel_name)

    generator = GoldenRatioAvatarGenerator(config)
    avatar = generator.generate_avatar(channel_name)

    # Create safe filename
    safe_name = "".join(c for c in channel_name if c.isalnum() or c in (" ", "-", "_")).rstrip()
    safe_name = safe_name.replace(" ", "_").lower()

    filepath = os.path.join(output_dir, f"{safe_name}_avatar.png")

    if generator.save_avatar(avatar, filepath):
        return filepath
    else:
        raise Exception("Failed to save avatar")


if __name__ == "__main__":
    # Example usage
    generator = GoldenRatioAvatarGenerator()

    # Generate test avatars
    test_channels = [
        ("Tech Insights", AvatarStyle.TECH),
        ("Creative Studio", AvatarStyle.CREATIVE),
        ("Business Pro", AvatarStyle.PROFESSIONAL),
        ("Art & Design", AvatarStyle.ORGANIC),
    ]

    for channel_name, style in test_channels:
        config = GoldenRatioConfig(style=style, include_text=True)
        gen = GoldenRatioAvatarGenerator(config)
        avatar = gen.generate_avatar(channel_name)

        filename = f"{channel_name.replace(' ', '_').lower()}_avatar.png"
        gen.save_avatar(avatar, f"test_avatars/{filename}")
        print(f"Generated avatar for {channel_name}")
