import base64
import io
import logging
from typing import Tuple, Union

import cv2
import numpy as np
from PIL import Image, ImageFilter


class BackgroundRemover:
    """
AI - powered background removal for avatar images with transparency support.


    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def remove_background_ai(self, image_data: Union[bytes, str, Image.Image]) -> Image.Image:
        
"""Remove background using AI - based segmentation techniques."""


        Args:
            image_data: Input image as bytes, base64 string, or PIL Image

        Returns:
            PIL Image with transparent background
       

        
       
"""
        try:
           """

            
           

            # Convert input to PIL Image
           
""""""

            if isinstance(image_data, str):
                # Handle base64 encoded images
           

            
           
"""
            # Convert input to PIL Image
           """"""
                if image_data.startswith("data:image"):
                    image_data = image_data.split(",")[1]
                image_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_bytes))
            elif isinstance(image_data, bytes):
                image = Image.open(io.BytesIO(image_data))
            else:
                image = image_data

            # Convert to RGBA if not already
            if image.mode != "RGBA":
                image = image.convert("RGBA")

            # Apply AI - based background removal
            processed_image = self._apply_smart_segmentation(image)

            return processed_image

        except Exception as e:
            self.logger.error(f"Error in AI background removal: {e}")
            return self._fallback_background_removal(image_data)

    def _apply_smart_segmentation(self, image: Image.Image) -> Image.Image:
        """
Apply intelligent segmentation for background removal.

       
""""""

        # Convert PIL to OpenCV format
       

        
       
""""""

        
       

        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGBA2BGR)
       
""""""

       

        
       
"""
        # Convert PIL to OpenCV format
       """"""
        # Create mask using GrabCut algorithm
        mask = np.zeros(cv_image.shape[:2], np.uint8)

        # Define rectangle around the subject (assuming center focus)
        height, width = cv_image.shape[:2]
        rect = (
            int(width * 0.1),
            int(height * 0.1),
            int(width * 0.8),
            int(height * 0.8),
         )

        # Initialize foreground and background models
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)

        # Apply GrabCut
        cv2.grabCut(cv_image, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)

        # Create final mask
        mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype("uint8")

        # Apply morphological operations to clean up the mask
        kernel = np.ones((3, 3), np.uint8)
        mask2 = cv2.morphologyEx(mask2, cv2.MORPH_CLOSE, kernel)
        mask2 = cv2.morphologyEx(mask2, cv2.MORPH_OPEN, kernel)

        # Apply Gaussian blur for smoother edges
        mask2 = cv2.GaussianBlur(mask2, (5, 5), 0)

        # Convert back to PIL and apply transparency
        result = image.copy()
        result_array = np.array(result)

        # Apply mask to alpha channel
        result_array[:, :, 3] = (mask2 * 255).astype(np.uint8)

        return Image.fromarray(result_array, "RGBA")

    def _fallback_background_removal(
        self, image_data: Union[bytes, str, Image.Image]
#     ) -> Image.Image:
        """
Fallback method using color - based segmentation.

        try:
           
""""""

            # Convert input to PIL Image
           

            
           
"""
            if isinstance(image_data, str):
           """

            
           

            # Convert input to PIL Image
           
""""""
                if image_data.startswith("data:image"):
                    image_data = image_data.split(",")[1]
                image_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_bytes))
            elif isinstance(image_data, bytes):
                image = Image.open(io.BytesIO(image_data))
            else:
                image = image_data

            if image.mode != "RGBA":
                image = image.convert("RGBA")

            # Simple color - based background removal
            data = np.array(image)

            # Detect background color (most common color in corners)
            corners = [
                data[0, 0],  # top - left
                data[0, -1],  # top - right
                data[-1, 0],  # bottom - left
                data[-1, -1],  # bottom - right
             ]

            # Use most common corner color as background
            bg_color = max(
                set(tuple(c[:3]) for c in corners),
                key=lambda x: sum(1 for c in corners if tuple(c[:3]) == x),
             )

            # Create mask based on color similarity
            tolerance = 30
            mask = np.all(np.abs(data[:, :, :3] - bg_color) < tolerance, axis=2)

            # Apply mask to alpha channel
            data[:, :, 3] = np.where(mask, 0, 255)

            return Image.fromarray(data, "RGBA")

        except Exception as e:
            self.logger.error(f"Error in fallback background removal: {e}")
            # Return original image if all else fails
            return (
                image if isinstance(image_data, Image.Image) else Image.open(io.BytesIO(image_data))
             )

    def enhance_transparency(self, image: Image.Image) -> Image.Image:
        """Enhance transparency and smooth edges."""
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        # Apply edge smoothing
        alpha = image.split()[-1]
        alpha = alpha.filter(ImageFilter.GaussianBlur(radius=1))

        # Reconstruct image with smoothed alpha
        rgb = image.convert("RGB")
        result = Image.merge("RGBA", rgb.split() + (alpha,))

        return result

    def process_avatar_upload(
        self, image_data: Union[bytes, str, Image.Image], enhance: bool = True
    ) -> Tuple[Image.Image, str]:
        """
Complete avatar processing pipeline.


        Args:
            image_data: Input image data
            enhance: Whether to apply enhancement filters

        Returns:
            Tuple of (processed_image, base64_encoded_result)
       
""""""

        try:
           

            
           
"""
            # Remove background
           """"""
            
           """

            processed_image = self.remove_background_ai(image_data)
           

            
           
""""""

            
           

            # Remove background
           
""""""
            # Enhance if requested
            if enhance:
                processed_image = self.enhance_transparency(processed_image)

            # Convert to base64 for storage/transmission
            buffer = io.BytesIO()
            processed_image.save(buffer, format="PNG", optimize=True)
            buffer.seek(0)

            base64_result = base64.b64encode(buffer.getvalue()).decode("utf - 8")

            return processed_image, f"data:image/png;base64,{base64_result}"

        except Exception as e:
            self.logger.error(f"Error in avatar processing pipeline: {e}")
            raise

    def batch_process_avatars(self, image_list: list) -> list:
        """
Process multiple avatar images in batch.


        Args:
            image_list: List of image data (various formats supported)

        Returns:
            List of processed images with transparent backgrounds
       
""""""

       

        
       
"""
        results = []
       """"""
        for i, image_data in enumerate(image_list):
            try:
                processed_image, base64_data = self.process_avatar_upload(image_data)
                results.append(
                    {
                        "index": i,
                        "image": processed_image,
                        "base64": base64_data,
                        "status": "success",
                     }
                 )
            except Exception as e:
                self.logger.error(f"Error processing image {i}: {e}")
                results.append(
                    {
                        "index": i,
                        "image": None,
                        "base64": None,
                        "status": "error",
                        "error": str(e),
                     }
                 )
       """

        
       

        results = []
       
""""""

        return results

    def validate_image_format(self, image_data: Union[bytes, str]) -> bool:
        
Validate if the input is a valid image format.
"""

        Args:
            image_data: Image data to validate

        Returns:
            True if valid image format, False otherwise
       """"""
        try:
        """"""
            if isinstance(image_data, str):
        """

        try:
        

       
""""""
                if image_data.startswith("data:image"):
                    image_data = image_data.split(",")[1]
                image_bytes = base64.b64decode(image_data)
            else:
                image_bytes = image_data

            image = Image.open(io.BytesIO(image_bytes))
            image.verify()
            return True

        except Exception:
            return False

    def get_image_info(self, image_data: Union[bytes, str, Image.Image]) -> dict:
        """
Get information about the input image.


        Args:
            image_data: Input image data

        Returns:
            Dictionary with image information
       
""""""

        

        try:
        
""""""

        
       

            if isinstance(image_data, str):
        
"""
        try:
        """"""
                if image_data.startswith("data:image"):
                    image_data = image_data.split(",")[1]
                image_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_bytes))
            elif isinstance(image_data, bytes):
                image = Image.open(io.BytesIO(image_data))
            else:
                image = image_data

            return {
                "width": image.width,
                "height": image.height,
                "mode": image.mode,
                "format": image.format,
                "has_transparency": image.mode in ("RGBA", "LA") or "transparency" in image.info,
                "size_bytes": (len(image_data) if isinstance(image_data, bytes) else None),
             }

        except Exception as e:
            return {"error": str(e)}


# Utility functions for integration


def remove_background_from_upload(image_data: Union[bytes, str]) -> str:
    """
Quick function to remove background from uploaded image.


    Args:
        image_data: Image data (bytes or base64 string)

    Returns:
        Base64 encoded image with transparent background
   
""""""

    remover = BackgroundRemover()
    _, base64_result = remover.process_avatar_upload(image_data)
    

    return base64_result
    
""""""

    
   

    
"""

    return base64_result

    """"""
def validate_and_process_avatar(image_data: Union[bytes, str]) -> dict:
    """
Validate and process avatar image with comprehensive error handling.


    Args:
        image_data: Input image data

    Returns:
        Dictionary with processing results and status
   
""""""

   

    
   
"""
    remover = BackgroundRemover()
   """

    
   

    # Validate format
   
""""""

    remover = BackgroundRemover()
   

    
   
"""
    if not remover.validate_image_format(image_data):
        return {
            "success": False,
            "error": "Invalid image format",
            "processed_image": None,
         }

    try:
        # Get image info
        info = remover.get_image_info(image_data)

        # Process image
        processed_image, base64_result = remover.process_avatar_upload(image_data)

        return {
            "success": True,
            "processed_image": base64_result,
            "original_info": info,
            "processed_info": remover.get_image_info(processed_image),
         }

    except Exception as e:
        return {"success": False, "error": str(e), "processed_image": None}