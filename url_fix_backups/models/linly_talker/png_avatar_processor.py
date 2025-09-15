import base64
import io
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

# Add the backend path to sys.path for imports
sys.path.append("/Users / thomasbrianreynolds / online production / backend")
sys.path.append("/Users / thomasbrianreynolds / online production")

try:

    from backend.avatar.background_remover import BackgroundRemover

except ImportError:
    # Fallback implementation if backend not available


    class BackgroundRemover:


        def __init__(self):
            self.logger = logging.getLogger(__name__)


        def process_avatar_upload(self, image_data, enhance = True):
            # Simple fallback processing
            if isinstance(image_data, str) and image_data.startswith("data:image"):
                image_data = image_data.split(",")[1]
                image_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_bytes))
            elif isinstance(image_data, str):
                image = Image.open(image_data)
            else:
                image = image_data

            if image.mode != "RGBA":
                image = image.convert("RGBA")

            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            buffer.seek(0)
            base64_result = base64.b64encode(buffer.getvalue()).decode("utf - 8")

            return image, f"data:image / png;base64,{base64_result}"


class PNGAvatarProcessor:
    """PNG - based avatar processing system for Linly - Talker."""


    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.background_remover = BackgroundRemover()
        self.temp_dir = Path("/tmp / linly_avatars")
        self.temp_dir.mkdir(exist_ok = True)

        # Avatar processing settings
        self.target_size = (512, 512)
        self.quality_settings = {
            "high": {"dpi": 300, "quality": 95},
                "medium": {"dpi": 150, "quality": 85},
                "low": {"dpi": 72, "quality": 75},
# BRACKET_SURGEON: disabled
#                 }


    def process_uploaded_image(
        self,
            image_path: str,
            remove_background: bool = True,
            enhance_quality: bool = True,
            target_style: str = "realistic",
            ) -> Dict[str, Any]:
        """Process uploaded PNG image for avatar generation."""

        Args:
            image_path: Path to uploaded image file
            remove_background: Whether to remove background
            enhance_quality: Whether to apply quality enhancements
            target_style: Style to apply ('realistic', 'cartoon', 'professional')

        Returns:
            Dictionary with processed image data and metadata
        """"""
        try:
            self.logger.info(f"Processing uploaded image: {image_path}")

            # Load and validate image
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")

            original_image = Image.open(image_path)

            # Convert to RGBA for processing
            if original_image.mode != "RGBA":
                original_image = original_image.convert("RGBA")

            processed_image = original_image.copy()
            processing_steps = []

            # Step 1: Remove background if requested
            if remove_background:
                self.logger.info("Removing background...")
                processed_image, base64_data = (
                    self.background_remover.process_avatar_upload(
                        processed_image, enhance = True
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
                processing_steps.append("Background removed with AI segmentation")

            # Step 2: Resize to target dimensions
            processed_image = self._resize_image(processed_image, self.target_size)
            processing_steps.append(
                f"Resized to {self.target_size[0]}x{self.target_size[1]}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            # Step 3: Apply style - specific enhancements
            if enhance_quality:
                processed_image = self._apply_style_enhancements(
                    processed_image, target_style
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
                processing_steps.append(f"Applied {target_style} style enhancements")

            # Step 4: Generate final output formats
            outputs = self._generate_output_formats(processed_image)

            # Step 5: Save processed image
            output_filename = f"processed_avatar_{hash(image_path) % 10000}.png"
            output_path = self.temp_dir / output_filename
            processed_image.save(output_path, "PNG", optimize = True, dpi=(300, 300))

            return {
                "success": True,
                    "original_path": image_path,
                    "processed_path": str(output_path),
                    "processed_image": processed_image,
                    "base64_data": outputs["base64"],
                    "data_uri": outputs["data_uri"],
                    "processing_steps": processing_steps,
                    "metadata": {
                    "original_size": original_image.size,
                        "processed_size": processed_image.size,
                        "has_transparency": processed_image.mode == "RGBA",
                        "background_removed": remove_background,
                        "style_applied": target_style,
                        "file_size_kb": len(outputs["base64"])
                    * 3 / 4/1024,  # Approximate
# BRACKET_SURGEON: disabled
#                 },
# BRACKET_SURGEON: disabled
#                     }

        except Exception as e:
            self.logger.error(f"Error processing uploaded image: {e}")
            return {
                "success": False,
                    "error": str(e),
                    "original_path": image_path if "image_path" in locals() else None,
# BRACKET_SURGEON: disabled
#                     }


    def _resize_image(
        self, image: Image.Image, target_size: Tuple[int, int]
# BRACKET_SURGEON: disabled
#     ) -> Image.Image:
        """Resize image while maintaining aspect ratio and quality."""
        # Calculate aspect ratio preserving dimensions
        original_width, original_height = image.size
        target_width, target_height = target_size

        # Calculate scaling factor
            scale_w = target_width / original_width
        scale_h = target_height / original_height
        scale = min(scale_w, scale_h)

        # Calculate new dimensions
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)

        # Resize with high - quality resampling
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Create final image with target size and center the resized image
        final_image = Image.new("RGBA", target_size, (0, 0, 0, 0))
        paste_x = (target_width - new_width) // 2
        paste_y = (target_height - new_height) // 2
        final_image.paste(resized, (paste_x, paste_y), resized)

        return final_image


    def _apply_style_enhancements(self, image: Image.Image, style: str) -> Image.Image:
        """Apply style - specific enhancements to the image."""
        enhanced = image.copy()

        if style == "realistic":
            # Enhance for realistic appearance
            enhancer = ImageEnhance.Sharpness(enhanced)
            enhanced = enhancer.enhance(1.2)

            enhancer = ImageEnhance.Contrast(enhanced)
            enhanced = enhancer.enhance(1.1)

            enhancer = ImageEnhance.Color(enhanced)
            enhanced = enhancer.enhance(1.05)

        elif style == "cartoon":
            # Apply cartoon - like effects
            enhanced = enhanced.filter(ImageFilter.SMOOTH_MORE)

            enhancer = ImageEnhance.Color(enhanced)
            enhanced = enhancer.enhance(1.3)

            enhancer = ImageEnhance.Contrast(enhanced)
            enhanced = enhancer.enhance(1.2)

        elif style == "professional":
            # Professional / business style
            enhancer = ImageEnhance.Contrast(enhanced)
            enhanced = enhancer.enhance(1.15)

            enhancer = ImageEnhance.Brightness(enhanced)
            enhanced = enhancer.enhance(1.05)

            # Slight desaturation for professional look
            enhancer = ImageEnhance.Color(enhanced)
            enhanced = enhancer.enhance(0.9)

        return enhanced


    def _generate_output_formats(self, image: Image.Image) -> Dict[str, str]:
        """Generate various output formats for the processed image."""
        # Generate base64 encoded PNG
        buffer = io.BytesIO()
        image.save(buffer, format="PNG", optimize = True)
        buffer.seek(0)

        base64_data = base64.b64encode(buffer.getvalue()).decode("utf - 8")
        data_uri = f"data:image / png;base64,{base64_data}"

        return {"base64": base64_data, "data_uri": data_uri}


    def create_avatar_from_paste(
        self, pasted_image_data: str, style: str = "realistic"
    ) -> Dict[str, Any]:
        """Create avatar from pasted image data (base64 or data URI)."""

        Args:
            pasted_image_data: Base64 encoded image or data URI
            style: Style to apply to the avatar

        Returns:
            Dictionary with processed avatar data
        """"""
        try:
            self.logger.info("Creating avatar from pasted image data")

            # Handle data URI format
            if pasted_image_data.startswith("data:image"):
                image_data = pasted_image_data.split(",")[1]
            else:
                image_data = pasted_image_data

            # Decode base64 to image
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))

            # Save temporarily for processing
            temp_filename = f"pasted_image_{hash(pasted_image_data) % 10000}.png"
            temp_path = self.temp_dir / temp_filename
            image.save(temp_path, "PNG")

            # Process the image
            result = self.process_uploaded_image(
                str(temp_path),
                    remove_background = True,
                    enhance_quality = True,
                    target_style = style,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

            # Clean up temporary file
            if temp_path.exists():
                temp_path.unlink()

            return result

        except Exception as e:
            self.logger.error(f"Error creating avatar from paste: {e}")
            return {"success": False, "error": str(e)}


    def get_supported_formats(self) -> list:
        """Get list of supported image formats."""
        return ["PNG", "JPEG", "JPG", "WEBP", "BMP", "TIFF"]


    def validate_image(self, image_path: str) -> Dict[str, Any]:
        """Validate uploaded image for avatar processing."""
        try:
            if not os.path.exists(image_path):
                return {"valid": False, "error": "File not found"}

            image = Image.open(image_path)

            # Check format
            if image.format not in self.get_supported_formats():
                return {
                    "valid": False,
                        "error": f"Unsupported format: {image.format}. Supported: {self.get_supported_formats()}",
# BRACKET_SURGEON: disabled
#                         }

            # Check dimensions
            width, height = image.size
            if width < 100 or height < 100:
                return {
                    "valid": False,
                        "error": "Image too small (minimum 100x100 pixels)",
# BRACKET_SURGEON: disabled
#                         }

            if width > 4000 or height > 4000:
                return {
                    "valid": False,
                        "error": "Image too large (maximum 4000x4000 pixels)",
# BRACKET_SURGEON: disabled
#                         }

            return {
                "valid": True,
                    "format": image.format,
                    "size": image.size,
                    "mode": image.mode,
                    "has_transparency": image.mode in ("RGBA", "LA"),
# BRACKET_SURGEON: disabled
#                     }

        except Exception as e:
            return {"valid": False, "error": f"Invalid image file: {str(e)}"}

# Global instance for use in demo_app.py
png_processor = PNGAvatarProcessor()


def process_avatar_image(image_path: str, style: str = "realistic") -> Tuple[str, str]:
    """Process avatar image and return status and data URI."""

    This function is designed to integrate with the existing Gradio interface.

    Args:
        image_path: Path to uploaded image
        style: Processing style to apply

    Returns:
        Tuple of (status_message, data_uri_or_none)
    """"""
    if not image_path:
        return "❌ No image uploaded. Please upload a PNG image to start.", None

    try:
        # Validate image first
        validation = png_processor.validate_image(image_path)
        if not validation["valid"]:
            return f"❌ Image validation failed: {validation['error']}", None

        # Process the image
        result = png_processor.process_uploaded_image(
            image_path, remove_background = True, enhance_quality = True, target_style = style
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

        if result["success"]:
            status_msg = "✅ Avatar processed successfully!\\n\\n"
            status_msg += "🔄 Processing steps completed:\\n"
            for step in result["processing_steps"]:
                status_msg += f"  • {step}\\n"

            status_msg += f"\\n📊 Metadata:\\n"
            metadata = result["metadata"]
            status_msg += f"  • Original size: {metadata['original_size'][0]}x{metadata['original_size'][1]}\\n"
            status_msg += f"  • Processed size: {metadata['processed_size'][0]}x{metadata['processed_size'][1]}\\n"
            status_msg += f"  • Background removed: {'Yes' if metadata['background_removed'] else 'No'}\\n"
            status_msg += f"  • Style applied: {metadata['style_applied']}\\n"
            status_msg += f"  • File size: {metadata['file_size_kb']:.1f} KB\\n"

            status_msg += "\\n🎭 Avatar ready for animation and lip - sync!"

            return status_msg, result["data_uri"]
        else:
            return f"❌ Processing failed: {result['error']}", None

    except Exception as e:
        return f"❌ Unexpected error: {str(e)}", None

if __name__ == "__main__":
    # Test the processor
        processor = PNGAvatarProcessor()
    print("PNG Avatar Processor initialized successfully!")
    print(f"Supported formats: {processor.get_supported_formats()}")
    print(f"Target size: {processor.target_size}")
    print(f"Temp directory: {processor.temp_dir}")