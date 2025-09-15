"""Paddle API integration for subscription and payment processing."""

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


class PaddleAPI(BaseMonetizationAPI):
    """Paddle API client for payment processing and subscription management."""

    def __init__(self, api_key: str, vendor_id: str, environment: str = "sandbox"):
        base_url = (
            "https://vendors.paddle.com/api/2.0"
            if environment == "production"
            else "https://sandbox - vendors.paddle.com/api/2.0"
# BRACKET_SURGEON: disabled
#         )

        super().__init__(
            api_key=api_key,
            base_url=base_url,
            rate_limit=60,  # Paddle allows 60 requests per minute
# BRACKET_SURGEON: disabled
#         )
        self.vendor_id = vendor_id
        self.environment = environment

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get Paddle API authentication headers."""
        return {"Content - Type": "application/json"}

    def _make_paddle_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a Paddle API request with vendor authentication."""
        # Paddle uses vendor_id and vendor_auth_code in the request body
        request_data = {
            "vendor_id": self.vendor_id,
            "vendor_auth_code": self.api_key,
            **data,
# BRACKET_SURGEON: disabled
#         }

        response = self._make_request("POST", endpoint, data=request_data)
        return response.json()

    def create_product(self, product: Product) -> ProductResponse:
        """Create a new product in Paddle."""
        try:
            product_data = {
                "name": product.title,
                "description": product.description,
                "base_price": product.price,
                "currency": product.currency,
                "initial_price": product.price,
                "recurring_price": (
                    product.price if product.metadata.get("subscription") else None
# BRACKET_SURGEON: disabled
#                 ),
                "trial_days": product.metadata.get("trial_days", 0),
                "billing_type": ("month" if product.metadata.get("subscription") else "one_off"),
                "billing_period": product.metadata.get("billing_period", 1),
                "icon": product.preview_images[0] if product.preview_images else None,
# BRACKET_SURGEON: disabled
#             }

            # Remove None values
            product_data = {k: v for k, v in product_data.items() if v is not None}

            response_data = self._make_paddle_request("/product/generate_pay_link", product_data)

            if response_data.get("success"):
                return ProductResponse(
                    success=True,
                    product_id=str(response_data.get("response", {}).get("product_id")),
                    product_url=response_data.get("response", {}).get("url"),
                    platform_data=response_data,
# BRACKET_SURGEON: disabled
#                 )
            else:
                return ProductResponse(
                    success=False,
                    error_message=response_data.get("error", {}).get("message", "Unknown error"),
# BRACKET_SURGEON: disabled
#                 )

        except Exception as e:
            logger.error(f"Failed to create Paddle product: {e}")
            return ProductResponse(success=False, error_message=str(e))

    def update_product(self, product_id: str, product: Product) -> ProductResponse:
        """Update an existing Paddle product."""
        try:
            update_data = {
                "product_id": product_id,
                "name": product.title,
                "description": product.description,
                "base_price": product.price,
                "currency": product.currency,
# BRACKET_SURGEON: disabled
#             }

            response_data = self._make_paddle_request("/product/update_product", update_data)

            if response_data.get("success"):
                return ProductResponse(
                    success=True, product_id=product_id, platform_data=response_data
# BRACKET_SURGEON: disabled
#                 )
            else:
                return ProductResponse(
                    success=False,
                    error_message=response_data.get("error", {}).get("message", "Unknown error"),
# BRACKET_SURGEON: disabled
#                 )

        except Exception as e:
            logger.error(f"Failed to update Paddle product {product_id}: {e}")
            return ProductResponse(success=False, error_message=str(e))

    def delete_product(self, product_id: str) -> bool:
        """Delete a Paddle product (actually just deactivate)."""
        try:
            response_data = self._make_paddle_request(
                "/product/update_product", {"product_id": product_id, "active": False}
# BRACKET_SURGEON: disabled
#             )
            return response_data.get("success", False)
        except Exception as e:
            logger.error(f"Failed to delete Paddle product {product_id}: {e}")
            return False

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get Paddle product details."""
        try:
            response_data = self._make_paddle_request(
                "/product/get_products", {"product_id": product_id}
# BRACKET_SURGEON: disabled
#             )

            if response_data.get("success"):
                products = response_data.get("response", [])
                return products[0] if products else None
            return None
        except Exception as e:
            logger.error(f"Failed to get Paddle product {product_id}: {e}")
            return None

    def list_products(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List all Paddle products."""
        try:
            response_data = self._make_paddle_request("/product/get_products", {})

            if response_data.get("success"):
                products = response_data.get("response", [])
                # Apply pagination manually since Paddle doesn't support it directly
                return products[offset : offset + limit]
            return []
        except Exception as e:
            logger.error(f"Failed to list Paddle products: {e}")
            return []

    def get_sales_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get Paddle sales analytics."""
        try:
            # Get transactions for the date range
            response_data = self._make_paddle_request(
                "/report/transactions",
                {
                    "from": start_date.strftime("%Y-%m-%d"),
                    "to": end_date.strftime("%Y-%m-%d"),
# BRACKET_SURGEON: disabled
#                 },
# BRACKET_SURGEON: disabled
#             )

            if response_data.get("success"):
                transactions = response_data.get("response", [])

                # Calculate analytics
                total_sales = len(transactions)
                total_revenue = sum(
                    float(transaction.get("earnings", 0)) for transaction in transactions
# BRACKET_SURGEON: disabled
#                 )

                return {
                    "platform": "Paddle",
                    "period": f"{start_date.date()} to {end_date.date()}",
                    "total_sales": total_sales,
                    "total_revenue": total_revenue,
                    "currency": "USD",
                    "transactions": transactions,
# BRACKET_SURGEON: disabled
#                 }
            else:
                return {"error": response_data.get("error", {}).get("message", "Unknown error")}

        except Exception as e:
            logger.error(f"Failed to get Paddle sales data: {e}")
            return {"error": str(e)}

    def create_subscription_plan(self, product: Product) -> ProductResponse:
        """Create a subscription plan in Paddle."""
        try:
            plan_data = {
                "plan_name": product.title,
                "plan_trial_days": product.metadata.get("trial_days", 0),
                "plan_length": product.metadata.get("billing_period", 1),
                "plan_type": product.metadata.get("plan_type", "month"),
                "main_currency_code": product.currency,
                "initial_price": product.price,
                "recurring_price": product.price,
# BRACKET_SURGEON: disabled
#             }

            response_data = self._make_paddle_request("/subscription/plans_create", plan_data)

            if response_data.get("success"):
                plan_id = response_data.get("response", {}).get("product_id")
                return ProductResponse(
                    success=True, product_id=str(plan_id), platform_data=response_data
# BRACKET_SURGEON: disabled
#                 )
            else:
                return ProductResponse(
                    success=False,
                    error_message=response_data.get("error", {}).get("message", "Unknown error"),
# BRACKET_SURGEON: disabled
#                 )

        except Exception as e:
            logger.error(f"Failed to create Paddle subscription plan: {e}")
            return ProductResponse(success=False, error_message=str(e))

    def get_subscription_analytics(self) -> Dict[str, Any]:
        """Get subscription analytics from Paddle."""
        try:
            response_data = self._make_paddle_request("/subscription/users", {})

            if response_data.get("success"):
                subscriptions = response_data.get("response", [])

                active_subscriptions = [
                    sub for sub in subscriptions if sub.get("state") == "active"
# BRACKET_SURGEON: disabled
#                 ]

                monthly_recurring_revenue = sum(
                    float(sub.get("next_payment", {}).get("amount", 0))
                    for sub in active_subscriptions
# BRACKET_SURGEON: disabled
#                 )

                return {
                    "platform": "Paddle",
                    "total_subscriptions": len(subscriptions),
                    "active_subscriptions": len(active_subscriptions),
                    "monthly_recurring_revenue": monthly_recurring_revenue,
                    "currency": "USD",
                    "subscriptions": subscriptions,
# BRACKET_SURGEON: disabled
#                 }
            else:
                return {"error": response_data.get("error", {}).get("message", "Unknown error")}

        except Exception as e:
            logger.error(f"Failed to get Paddle subscription analytics: {e}")
            return {"error": str(e)}

    def create_checkout_url(
        self, product_id: str, custom_data: Dict[str, Any] = None
    ) -> Optional[str]:
        """Create a checkout URL for a product."""
        try:
            checkout_data = {
                "product_id": product_id,
                "title": custom_data.get("title", "Purchase"),
                "webhook_url": custom_data.get("webhook_url"),
                "prices": custom_data.get("prices", []),
                "custom_message": custom_data.get("custom_message"),
# BRACKET_SURGEON: disabled
#             }

            # Remove None values
            checkout_data = {k: v for k, v in checkout_data.items() if v is not None}

            response_data = self._make_paddle_request("/product/generate_pay_link", checkout_data)

            if response_data.get("success"):
                return response_data.get("response", {}).get("url")
            return None

        except Exception as e:
            logger.error(f"Failed to create Paddle checkout URL: {e}")
            return None

    def health_check(self) -> bool:
        """Check Paddle API health."""
        try:
            response_data = self._make_paddle_request("/product/get_products", {})
            return response_data.get("success", False)
        except Exception as e:
            logger.warning(f"Paddle health check failed: {e}")
            return False