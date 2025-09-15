"""SendOwl API integration for digital product delivery and affiliate management."""

import base64
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


class SendOwlAPI(BaseMonetizationAPI):
    """SendOwl API client for digital product delivery and sales."""

    def __init__(self, api_key: str, api_secret: str):
        super().__init__(
            api_key=api_key,
            base_url="https://www.sendowl.com/api/v1",
            rate_limit=120,  # SendOwl allows 120 requests per minute
# BRACKET_SURGEON: disabled
#         )
        self.api_secret = api_secret

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get SendOwl API authentication headers using Basic Auth."""
        credentials = f"{self.api_key}:{self.api_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        return {
            "Authorization": f"Basic {encoded_credentials}",
            "Content - Type": "application/json",
            "Accept": "application/json",
# BRACKET_SURGEON: disabled
#         }

    def create_product(self, product: Product) -> ProductResponse:
        """Create a new product in SendOwl."""
        try:
            product_data = {
                "product": {
                    "name": product.title,
                    "price": str(product.price),
                    "price_currency": product.currency,
                    "product_type": "digital",
                    "description": product.description,
                    "tags": ", ".join(product.tags) if product.tags else "",
                    "self_hosted": True,
                    "license_type": product.metadata.get("license_type", "single"),
                    "download_limit": product.metadata.get("download_limit", 3),
                    "link_expiry": product.metadata.get("link_expiry", 72),  # hours
                    "instant_buy": product.metadata.get("instant_buy", True),
                    "add_to_cart": product.metadata.get("add_to_cart", True),
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             }

            response = self._make_request("POST", "/products", data=product_data)
            product_response = response.json()

            # Upload digital files if provided
            product_id = product_response["product"]["id"]
            if product.digital_files:
                self._upload_digital_files(product_id, product.digital_files)

            return ProductResponse(
                success=True,
                product_id=str(product_id),
                product_url=product_response["product"].get("sales_page_url"),
                platform_data=product_response,
# BRACKET_SURGEON: disabled
#             )

        except Exception as e:
            logger.error(f"Failed to create SendOwl product: {e}")
            return ProductResponse(success=False, error_message=str(e))

    def update_product(self, product_id: str, product: Product) -> ProductResponse:
        """Update an existing SendOwl product."""
        try:
            product_data = {
                "product": {
                    "name": product.title,
                    "price": str(product.price),
                    "price_currency": product.currency,
                    "description": product.description,
                    "tags": ", ".join(product.tags) if product.tags else "",
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             }

            response = self._make_request("PUT", f"/products/{product_id}", data=product_data)
            product_response = response.json()

            return ProductResponse(
                success=True,
                product_id=product_id,
                product_url=product_response["product"].get("sales_page_url"),
                platform_data=product_response,
# BRACKET_SURGEON: disabled
#             )

        except Exception as e:
            logger.error(f"Failed to update SendOwl product {product_id}: {e}")
            return ProductResponse(success=False, error_message=str(e))

    def delete_product(self, product_id: str) -> bool:
        """Delete a SendOwl product."""
        try:
            self._make_request("DELETE", f"/products/{product_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete SendOwl product {product_id}: {e}")
            return False

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get SendOwl product details."""
        try:
            response = self._make_request("GET", f"/products/{product_id}")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get SendOwl product {product_id}: {e}")
            return None

    def list_products(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List SendOwl products."""
        try:
            params = {
                "per_page": min(limit, 100),  # SendOwl max is 100
                "page": (offset // limit) + 1,
# BRACKET_SURGEON: disabled
#             }

            response = self._make_request("GET", "/products", params=params)
            products_data = response.json()

            return products_data.get("products", [])
        except Exception as e:
            logger.error(f"Failed to list SendOwl products: {e}")
            return []

    def get_sales_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get SendOwl sales analytics."""
        try:
            params = {
                "from": start_date.strftime("%Y-%m-%d"),
                "to": end_date.strftime("%Y-%m-%d"),
                "per_page": 100,
# BRACKET_SURGEON: disabled
#             }

            response = self._make_request("GET", "/orders", params=params)
            orders_data = response.json()
            orders = orders_data.get("orders", [])

            # Calculate analytics
            total_sales = len(orders)
            total_revenue = sum(float(order.get("total", 0)) for order in orders)

            # Get refund data
            refunds_response = self._make_request("GET", "/refunds", params=params)
            refunds_data = refunds_response.json()
            refunds = refunds_data.get("refunds", [])

            total_refunds = sum(float(refund.get("amount", 0)) for refund in refunds)

            return {
                "platform": "SendOwl",
                "period": f"{start_date.date()} to {end_date.date()}",
                "total_sales": total_sales,
                "total_revenue": total_revenue,
                "total_refunds": total_refunds,
                "net_revenue": total_revenue - total_refunds,
                "currency": "USD",
                "orders": orders,
                "refunds": refunds,
# BRACKET_SURGEON: disabled
#             }

        except Exception as e:
            logger.error(f"Failed to get SendOwl sales data: {e}")
            return {"error": str(e)}

    def create_discount_code(
        self, code: str, discount_percent: float, product_ids: List[str] = None
    ) -> Dict[str, Any]:
        """Create a discount code in SendOwl."""
        try:
            discount_data = {
                "discount": {
                    "name": code,
                    "code": code,
                    "discount_type": "percentage",
                    "amount": str(discount_percent),
                    "usage_limit": 1000,  # Default usage limit
                    "active": True,
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             }

            # Add product restrictions if specified
            if product_ids:
                discount_data["discount"]["product_ids"] = product_ids

            response = self._make_request("POST", "/discounts", data=discount_data)
            return response.json()

        except Exception as e:
            logger.error(f"Failed to create SendOwl discount code: {e}")
            return {"error": str(e)}

    def get_affiliate_data(self) -> Dict[str, Any]:
        """Get affiliate program data from SendOwl."""
        try:
            response = self._make_request("GET", "/affiliates")
            affiliates_data = response.json()

            # Get affiliate commissions
            commissions_response = self._make_request("GET", "/affiliate_commissions")
            commissions_data = commissions_response.json()

            return {
                "platform": "SendOwl",
                "affiliates": affiliates_data.get("affiliates", []),
                "commissions": commissions_data.get("affiliate_commissions", []),
                "total_affiliates": len(affiliates_data.get("affiliates", [])),
                "total_commissions": sum(
                    float(commission.get("amount", 0))
                    for commission in commissions_data.get("affiliate_commissions", [])
# BRACKET_SURGEON: disabled
#                 ),
# BRACKET_SURGEON: disabled
#             }

        except Exception as e:
            logger.error(f"Failed to get SendOwl affiliate data: {e}")
            return {"error": str(e)}

    def _upload_digital_files(self, product_id: str, file_paths: List[str]):
        """Upload digital files to a SendOwl product."""
        for file_path in file_paths:
            try:
                # This would involve multipart file upload
                # Implementation depends on file handling strategy
                logger.info(
                    f"Would upload digital file {file_path} to SendOwl product {product_id}"
# BRACKET_SURGEON: disabled
#                 )
            except Exception as e:
                logger.error(f"Failed to upload digital file {file_path}: {e}")

    def create_bundle(
        self, bundle_name: str, product_ids: List[str], bundle_price: float
    ) -> Dict[str, Any]:
        """Create a product bundle in SendOwl."""
        try:
            bundle_data = {
                "package": {
                    "name": bundle_name,
                    "price": str(bundle_price),
                    "product_ids": product_ids,
                    "package_type": "bundle",
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             }

            response = self._make_request("POST", "/packages", data=bundle_data)
            return response.json()

        except Exception as e:
            logger.error(f"Failed to create SendOwl bundle: {e}")
            return {"error": str(e)}

    def get_download_analytics(self) -> Dict[str, Any]:
        """Get download analytics from SendOwl."""
        try:
            response = self._make_request("GET", "/downloads")
            downloads_data = response.json()
            downloads = downloads_data.get("downloads", [])

            # Analyze download patterns
            total_downloads = len(downloads)
            unique_customers = len(
                set(
                    download.get("buyer_email")
                    for download in downloads
                    if download.get("buyer_email")
# BRACKET_SURGEON: disabled
#                 )
# BRACKET_SURGEON: disabled
#             )

            return {
                "platform": "SendOwl",
                "total_downloads": total_downloads,
                "unique_customers": unique_customers,
                "average_downloads_per_customer": total_downloads / max(unique_customers, 1),
                "downloads": downloads,
# BRACKET_SURGEON: disabled
#             }

        except Exception as e:
            logger.error(f"Failed to get SendOwl download analytics: {e}")
            return {"error": str(e)}

    def health_check(self) -> bool:
        """Check SendOwl API health."""
        try:
            response = self._make_request("GET", "/products", params={"per_page": 1})
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"SendOwl health check failed: {e}")
            return False