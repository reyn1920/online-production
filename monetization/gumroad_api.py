"""Gumroad API integration for digital product sales and creator tools."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base_monetization import (BaseMonetizationAPI, Product, ProductCreationError,
    ProductResponse)

logger = logging.getLogger(__name__)


class GumroadAPI(BaseMonetizationAPI):
    """Gumroad API client for digital product sales and management."""


    def __init__(self, access_token: str):
        super().__init__(
            api_key = access_token,
                base_url="https://api.gumroad.com / v2",
                rate_limit = 60,  # Gumroad allows 60 requests per minute
        )
        self.access_token = access_token


    def _get_auth_headers(self) -> Dict[str, str]:
        """Get Gumroad API authentication headers."""
        return {
            "Authorization": f"Bearer {self.access_token}",
                "Content - Type": "application / json",
                }


    def create_product(self, product: Product) -> ProductResponse:
        """Create a new product on Gumroad."""
        try:
            product_data = {
                "name": product.title,
                    "description": product.description,
                    "price": int(product.price * 100),  # Gumroad uses cents
                "currency": product.currency,
                    "content_type": "digital",
                    "tags": ",".join(product.tags) if product.tags else "",
                    "require_shipping": False,
                    "published": False,  # Start as draft
                "shown_on_profile": True,
                    "file_info": {},
                    "preview_url": (
                    product.preview_images[0] if product.preview_images else None
                ),
                    "variants_enabled": product.metadata.get("variants_enabled", False),
                    "affiliate_program": product.metadata.get("affiliate_program", False),
                    "max_purchase_count": product.metadata.get("max_purchase_count", 0),
                    }

            # Remove None values
            product_data = {k: v for k, v in product_data.items() if v is not None}

            response = self._make_request("POST", "/products", data = product_data)
            product_response = response.json()

            if product_response.get("success"):
                product_info = product_response["product"]

                # Upload digital files if provided
                if product.digital_files:
                    self._upload_digital_files(
                        product_info["id"], product.digital_files
                    )

                return ProductResponse(
                    success = True,
                        product_id = product_info["id"],
                        product_url = product_info.get("short_url"),
                        platform_data = product_response,
                        )
            else:
                return ProductResponse(
                    success = False,
                        error_message = product_response.get("message", "Unknown error"),
                        )

        except Exception as e:
            logger.error(f"Failed to create Gumroad product: {e}")
            return ProductResponse(success = False, error_message = str(e))


    def update_product(self, product_id: str, product: Product) -> ProductResponse:
        """Update an existing Gumroad product."""
        try:
            product_data = {
                "name": product.title,
                    "description": product.description,
                    "price": int(product.price * 100),  # Gumroad uses cents
                "currency": product.currency,
                    "tags": ",".join(product.tags) if product.tags else "",
                    }

            response = self._make_request(
                "PUT", f"/products/{product_id}", data = product_data
            )
            product_response = response.json()

            if product_response.get("success"):
                return ProductResponse(
                    success = True,
                        product_id = product_id,
                        product_url = product_response["product"].get("short_url"),
                        platform_data = product_response,
                        )
            else:
                return ProductResponse(
                    success = False,
                        error_message = product_response.get("message", "Unknown error"),
                        )

        except Exception as e:
            logger.error(f"Failed to update Gumroad product {product_id}: {e}")
            return ProductResponse(success = False, error_message = str(e))


    def delete_product(self, product_id: str) -> bool:
        """Delete a Gumroad product."""
        try:
            response = self._make_request("DELETE", f"/products/{product_id}")
            response_data = response.json()
            return response_data.get("success", False)
        except Exception as e:
            logger.error(f"Failed to delete Gumroad product {product_id}: {e}")
            return False


    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get Gumroad product details."""
        try:
            response = self._make_request("GET", f"/products/{product_id}")
            response_data = response.json()

            if response_data.get("success"):
                return response_data.get("product")
            return None
        except Exception as e:
            logger.error(f"Failed to get Gumroad product {product_id}: {e}")
            return None


    def list_products(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List Gumroad products."""
        try:
            params = {
                "page": (offset // limit) + 1,
                    "per_page": min(limit, 100),  # Gumroad max is 100
            }

            response = self._make_request("GET", "/products", params = params)
            response_data = response.json()

            if response_data.get("success"):
                return response_data.get("products", [])
            return []
        except Exception as e:
            logger.error(f"Failed to list Gumroad products: {e}")
            return []


    def get_sales_data(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get Gumroad sales analytics."""
        try:
            params = {
                "after": start_date.strftime("%Y-%m-%d"),
                    "before": end_date.strftime("%Y-%m-%d"),
                    "page": 1,
                    "per_page": 100,
                    }

            all_sales = []
            page = 1

            while True:
                params["page"] = page
                response = self._make_request("GET", "/sales", params = params)
                response_data = response.json()

                if not response_data.get("success"):
                    break

                sales = response_data.get("sales", [])
                if not sales:
                    break

                all_sales.extend(sales)
                page += 1

                # Limit to prevent infinite loops
                if page > 100:
                    break

            # Calculate analytics
            total_sales = len(all_sales)
            total_revenue = sum(
                float(sale.get("price", 0)) / 100  # Convert from cents
                for sale in all_sales
            )

            # Get refund data
            refunds = [sale for sale in all_sales if sale.get("refunded")]
            total_refunds = sum(
                float(refund.get("price", 0)) / 100 for refund in refunds
            )

            return {
                "platform": "Gumroad",
                    "period": f"{start_date.date()} to {end_date.date()}",
                    "total_sales": total_sales,
                    "total_revenue": total_revenue,
                    "total_refunds": total_refunds,
                    "net_revenue": total_revenue - total_refunds,
                    "currency": "USD",
                    "sales": all_sales,
                    "refunds": refunds,
                    }

        except Exception as e:
            logger.error(f"Failed to get Gumroad sales data: {e}")
            return {"error": str(e)}


    def publish_product(self, product_id: str) -> bool:
        """Publish a draft product on Gumroad."""
        try:
            response = self._make_request("PUT", f"/products/{product_id}/enable")
            response_data = response.json()
            return response_data.get("success", False)
        except Exception as e:
            logger.error(f"Failed to publish Gumroad product {product_id}: {e}")
            return False


    def create_discount_code(
        self, product_id: str, code: str, discount_percent: float, max_uses: int = 100
    ) -> Dict[str, Any]:
        """Create a discount code for a Gumroad product."""
        try:
            discount_data = {
                "name": code,
                    "amount_cents": int(discount_percent * 100),  # Convert to basis points
                "max_purchase_count": max_uses,
                    "universal": False,  # Product - specific discount
            }

            response = self._make_request(
                "POST", f"/products/{product_id}/offer_codes", data = discount_data
            )
            return response.json()

        except Exception as e:
            logger.error(f"Failed to create Gumroad discount code: {e}")
            return {"error": str(e)}


    def get_user_info(self) -> Dict[str, Any]:
        """Get Gumroad user / seller information."""
        try:
            response = self._make_request("GET", "/user")
            response_data = response.json()

            if response_data.get("success"):
                return response_data.get("user", {})
            return {"error": response_data.get("message", "Unknown error")}

        except Exception as e:
            logger.error(f"Failed to get Gumroad user info: {e}")
            return {"error": str(e)}


    def get_subscriber_data(self) -> Dict[str, Any]:
        """Get subscriber / follower data from Gumroad."""
        try:
            response = self._make_request("GET", "/subscribers")
            response_data = response.json()

            if response_data.get("success"):
                subscribers = response_data.get("subscribers", [])
                return {
                    "platform": "Gumroad",
                        "total_subscribers": len(subscribers),
                        "subscribers": subscribers,
                        }
            return {"error": response_data.get("message", "Unknown error")}

        except Exception as e:
            logger.error(f"Failed to get Gumroad subscriber data: {e}")
            return {"error": str(e)}


    def _upload_digital_files(self, product_id: str, file_paths: List[str]):
        """Upload digital files to a Gumroad product."""
        for file_path in file_paths:
            try:
                # This would involve multipart file upload
                # Implementation depends on file handling strategy
                logger.info(
                    f"Would upload digital file {file_path} to Gumroad product {product_id}"
                )
            except Exception as e:
                logger.error(f"Failed to upload digital file {file_path}: {e}")


    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get comprehensive analytics summary from Gumroad."""
        try:
            # Get user info for basic stats
            user_info = self.get_user_info()

            # Get recent sales (last 30 days)
            end_date = datetime.now()
            start_date = datetime.now().replace(day = 1)  # First day of current month
            sales_data = self.get_sales_data(start_date, end_date)

            # Get subscriber data
            subscriber_data = self.get_subscriber_data()

            return {
                "platform": "Gumroad",
                    "user_info": user_info,
                    "monthly_sales": sales_data,
                    "subscribers": subscriber_data,
                    "generated_at": datetime.now().isoformat(),
                    }

        except Exception as e:
            logger.error(f"Failed to get Gumroad analytics summary: {e}")
            return {"error": str(e)}


    def health_check(self) -> bool:
        """Check Gumroad API health."""
        try:
            response = self._make_request("GET", "/user")
            response_data = response.json()
            return response_data.get("success", False)
        except Exception as e:
            logger.warning(f"Gumroad health check failed: {e}")
            return False
