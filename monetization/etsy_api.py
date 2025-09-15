"""Etsy API integration for automated product creation and sales."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base_monetization import (
    BaseMonetizationAPI,
    Product,
    ProductResponse,
# BRACKET_SURGEON: disabled
# )

logger = logging.getLogger(__name__)


class EtsyAPI(BaseMonetizationAPI):
    """Etsy API client for automated product management."""

    def __init__(self, api_key: str, shop_id: str, access_token: str = None):
        super().__init__(
            api_key=api_key,
            base_url="https://openapi.etsy.com/v3",
            rate_limit=10,  # Etsy allows 10 requests per second
# BRACKET_SURGEON: disabled
#         )
        self.shop_id = shop_id
        self.access_token = access_token

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get Etsy API authentication headers."""
        headers = {"x - api - key": self.api_key, "Content - Type": "application/json"}

        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        return headers

    def create_product(self, product: Product) -> ProductResponse:
        """Create a new listing on Etsy."""
        try:
            # Map our product to Etsy's listing format
            listing_data = {
                "title": product.title[:140],  # Etsy title limit
                "description": product.description,
                "price": product.price,
                "quantity": 999,  # Digital products can have high quantity
                "who_made": "i_did",
                "when_made": "2020_2024",
                "is_supply": False,
                "state": "draft",  # Start as draft
                "processing_min": 1,
                "processing_max": 3,
                "tags": (product.tags[:13] if product.tags else []),  # Etsy allows max 13 tags
                "materials": ["digital"],
                "shipping_template_id": None,  # Digital products don't need shipping
                "is_digital": True,
# BRACKET_SURGEON: disabled
#             }

            # Add category if provided
            if product.category:
                listing_data["taxonomy_id"] = self._get_taxonomy_id(product.category)

            response = self._make_request(
                "POST", f"/application/shops/{self.shop_id}/listings", data=listing_data
# BRACKET_SURGEON: disabled
#             )

            listing = response.json()

            # Upload digital files if provided
            if product.digital_files:
                self._upload_digital_files(listing["listing_id"], product.digital_files)

            # Upload preview images if provided
            if product.preview_images:
                self._upload_listing_images(listing["listing_id"], product.preview_images)

            return ProductResponse(
                success=True,
                product_id=str(listing["listing_id"]),
                product_url=listing.get("url"),
                platform_data=listing,
# BRACKET_SURGEON: disabled
#             )

        except Exception as e:
            logger.error(f"Failed to create Etsy listing: {e}")
            return ProductResponse(success=False, error_message=str(e))

    def update_product(self, product_id: str, product: Product) -> ProductResponse:
        """Update an existing Etsy listing."""
        try:
            listing_data = {
                "title": product.title[:140],
                "description": product.description,
                "price": product.price,
                "tags": product.tags[:13] if product.tags else [],
# BRACKET_SURGEON: disabled
#             }

            response = self._make_request(
                "PUT",
                f"/application/shops/{self.shop_id}/listings/{product_id}",
                data=listing_data,
# BRACKET_SURGEON: disabled
#             )

            listing = response.json()

            return ProductResponse(
                success=True,
                product_id=product_id,
                product_url=listing.get("url"),
                platform_data=listing,
# BRACKET_SURGEON: disabled
#             )

        except Exception as e:
            logger.error(f"Failed to update Etsy listing {product_id}: {e}")
            return ProductResponse(success=False, error_message=str(e))

    def delete_product(self, product_id: str) -> bool:
        """Delete an Etsy listing."""
        try:
            self._make_request("DELETE", f"/application/shops/{self.shop_id}/listings/{product_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete Etsy listing {product_id}: {e}")
            return False

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get Etsy listing details."""
        try:
            response = self._make_request("GET", f"/application/listings/{product_id}")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get Etsy listing {product_id}: {e}")
            return None

    def list_products(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List shop listings from Etsy."""
        try:
            params = {
                "limit": min(limit, 100),  # Etsy max limit is 100
                "offset": offset,
                "state": "active",
# BRACKET_SURGEON: disabled
#             }

            response = self._make_request(
                "GET", f"/application/shops/{self.shop_id}/listings", params=params
# BRACKET_SURGEON: disabled
#             )

            return response.json().get("results", [])
        except Exception as e:
            logger.error(f"Failed to list Etsy products: {e}")
            return []

    def get_sales_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get Etsy sales analytics."""
        try:
            params = {
                "min_created": int(start_date.timestamp()),
                "max_created": int(end_date.timestamp()),
                "limit": 100,
# BRACKET_SURGEON: disabled
#             }

            response = self._make_request(
                "GET", f"/application/shops/{self.shop_id}/receipts", params=params
# BRACKET_SURGEON: disabled
#             )

            receipts = response.json().get("results", [])

            # Calculate analytics
            total_sales = len(receipts)
            total_revenue = sum(float(receipt.get("grandtotal", 0)) for receipt in receipts)

            return {
                "platform": "Etsy",
                "period": f"{start_date.date()} to {end_date.date()}",
                "total_sales": total_sales,
                "total_revenue": total_revenue,
                "currency": "USD",
                "receipts": receipts,
# BRACKET_SURGEON: disabled
#             }

        except Exception as e:
            logger.error(f"Failed to get Etsy sales data: {e}")
            return {"error": str(e)}

    def _get_taxonomy_id(self, category: str) -> Optional[int]:
        """Get Etsy taxonomy ID for a category."""
        # This would typically involve calling Etsy's taxonomy API
        # For now, return a default digital category ID
        category_mapping = {
            "digital_art": 69150467,
            "templates": 69150467,
            "printables": 69150467,
            "ebooks": 69150467,
            "courses": 69150467,
# BRACKET_SURGEON: disabled
#         }
        return category_mapping.get(category.lower(), 69150467)

    def _upload_digital_files(self, listing_id: str, file_paths: List[str]):
        """Upload digital files to an Etsy listing."""
        for file_path in file_paths:
            try:
                # This would involve multipart file upload
                # Implementation depends on file handling strategy
                logger.info(f"Would upload digital file {file_path} to listing {listing_id}")
            except Exception as e:
                logger.error(f"Failed to upload digital file {file_path}: {e}")

    def _upload_listing_images(self, listing_id: str, image_paths: List[str]):
        """Upload preview images to an Etsy listing."""
        for image_path in image_paths:
            try:
                # This would involve multipart image upload
                logger.info(f"Would upload image {image_path} to listing {listing_id}")
            except Exception as e:
                logger.error(f"Failed to upload image {image_path}: {e}")

    def activate_listing(self, listing_id: str) -> bool:
        """Activate a draft listing to make it live."""
        try:
            response = self._make_request(
                "PUT",
                f"/application/shops/{self.shop_id}/listings/{listing_id}",
                data={"state": "active"},
# BRACKET_SURGEON: disabled
#             )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to activate Etsy listing {listing_id}: {e}")
            return False

    def get_shop_info(self) -> Optional[Dict[str, Any]]:
        """Get shop information and statistics."""
        try:
            response = self._make_request("GET", f"/application/shops/{self.shop_id}")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get Etsy shop info: {e}")
            return None