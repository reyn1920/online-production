#!/usr/bin/env python3
""""""
Affiliate Credentials Router

Manages affiliate dashboard credentials and authentication.
""""""

import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.agents.stealth_automation_agent import AffiliateDashboard

router = APIRouter(prefix="/api/affiliates", tags=["affiliate-credentials"])
security = HTTPBearer()
logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path("intelligence.db")


class AffiliateCredentialsService:
    """Service for managing affiliate credentials"""

    def __init__(self):
        self.db_path = DB_PATH
        self.encryption_key = self._get_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key) if self.encryption_key else None

    def _get_encryption_key(self) -> Optional[bytes]:
        """Get encryption key from environment or generate one"""
        key_str = os.getenv("AFFILIATE_ENCRYPTION_KEY")
        if key_str:
            return key_str.encode()

        # For development, use a default key (NOT for production)
        logger.warning("Using default encryption key - set AFFILIATE_ENCRYPTION_KEY in production")
        return Fernet.generate_key()

    def _decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt stored password"""
        if not self.cipher_suite:
            return "[Encryption not available]"

        try:
            return self.cipher_suite.decrypt(encrypted_password.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt password: {e}")
            return "[Decryption failed]"

    def get_all_credentials(self) -> Dict[str, Any]:
        """Retrieve all affiliate dashboard credentials"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Get all affiliate dashboards
                cursor.execute(
                    """"""
                    SELECT
                        id,
                        platform_name,
                        login_url,
                        username,
                        encrypted_password,
                        dashboard_url,
                        last_login_attempt,
                        login_success_rate,
                        notes,
                        created_at,
                        updated_at,
                        COALESCE(is_active, 1) as is_active
                    FROM affiliate_dashboards
                    ORDER BY platform_name
                """"""
# BRACKET_SURGEON: disabled
#                 )

                rows = cursor.fetchall()

                credentials = []
                for row in rows:
                    # Decrypt password
                    decrypted_password = self._decrypt_password(row["encrypted_password"])

                    # Determine status based on recent activity
                    status = self._determine_status(
                        row["last_login_attempt"], row["login_success_rate"]
# BRACKET_SURGEON: disabled
#                     )

                    credential = {
                        "id": row["id"],
                        "programName": row["platform_name"],
                        "category": self._get_program_category(row["platform_name"]),
                        "dashboardUrl": row["dashboard_url"] or row["login_url"],
                        "username": row["username"],
                        "password": decrypted_password,
                        "lastAccess": row["last_login_attempt"],
                        "successRate": row["login_success_rate"] or 0,
                        "status": status,
                        "notes": row["notes"],
                        "createdAt": row["created_at"],
                        "updatedAt": row["updated_at"],
                        "isActive": bool(row["is_active"]),
# BRACKET_SURGEON: disabled
#                     }
                    credentials.append(credential)

                # Calculate stats
                stats = self._calculate_stats(credentials)

                return {
                    "credentials": credentials,
                    "stats": stats,
                    "total": len(credentials),
# BRACKET_SURGEON: disabled
#                 }

        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            raise HTTPException(status_code=500, detail="Database error")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    def _determine_status(self, last_login: Optional[str], success_rate: Optional[float]) -> str:
        """Determine credential status based on activity"""
        if not last_login:
            return "pending"

        # Parse last login date
        try:
            last_login_date = datetime.fromisoformat(last_login.replace("Z", "+00:00"))
            days_since_login = (datetime.now() - last_login_date.replace(tzinfo=None)).days

            if success_rate and success_rate >= 80 and days_since_login <= 30:
                return "active"
            elif success_rate and success_rate < 50:
                return "inactive"
            else:
                return "pending"
        except Exception:
            return "pending"

    def _get_program_category(self, platform_name: str) -> str:
        """Categorize affiliate program"""
        platform_lower = platform_name.lower()

        if any(keyword in platform_lower for keyword in ["clickbank", "cb"]):
            return "Digital Products"
        elif any(keyword in platform_lower for keyword in ["amazon", "amzn"]):
            return "E-commerce"
        elif any(keyword in platform_lower for keyword in ["commission", "cj", "shareasale"]):
            return "Network"
        elif any(keyword in platform_lower for keyword in ["software", "saas", "app"]):
            return "Software"
        elif any(keyword in platform_lower for keyword in ["finance", "trading", "crypto"]):
            return "Finance"
        else:
            return "General"

    def _calculate_stats(self, credentials: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics"""
        total = len(credentials)
        active = sum(1 for c in credentials if c["status"] == "active")

        # Find most recent access
        last_access = "Never"
        if credentials:
            recent_accesses = [c["lastAccess"] for c in credentials if c["lastAccess"]]
            if recent_accesses:
                most_recent = max(recent_accesses)
                try:
                    last_access_date = datetime.fromisoformat(most_recent.replace("Z", "+00:00"))
                    last_access = last_access_date.strftime("%b %d, %Y")
                except Exception:
                    last_access = "Unknown"

        # Calculate security score (simplified)
        security_score = 98  # Base score
        if total > 0:
            # Reduce score for inactive credentials
            inactive_penalty = (total - active) * 2
            security_score = max(50, security_score - inactive_penalty)

        return {
            "totalCredentials": total,
            "activeCredentials": active,
            "inactiveCredentials": total - active,
            "lastAccess": last_access,
            "securityScore": security_score,
# BRACKET_SURGEON: disabled
#         }

    def test_credential_login(self, credential_id: str) -> Dict[str, Any]:
        """Test login for a specific credential"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Get credential details
                cursor.execute(
                    """"""
                    SELECT platform_name, login_url, username, encrypted_password
                    FROM affiliate_dashboards
                    WHERE id = ?
                ""","""
                    (credential_id,),
# BRACKET_SURGEON: disabled
#                 )

                row = cursor.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Credential not found")

                # Decrypt password
                decrypted_password = self._decrypt_password(row["encrypted_password"])

                # Create affiliate dashboard instance for testing
                dashboard = AffiliateDashboard(
                    platform_name=row["platform_name"],
                    login_url=row["login_url"],
                    username=row["username"],
                    password=decrypted_password,
# BRACKET_SURGEON: disabled
#                 )

                # Attempt login test
                test_result = dashboard.test_login()

                # Update database with test results
                cursor.execute(
                    """"""
                    UPDATE affiliate_dashboards
                    SET last_login_attempt = ?,
                        login_success_rate = COALESCE(login_success_rate, 0) * 0.9 + ? * 0.1,
                        updated_at = ?
                    WHERE id = ?
                ""","""
                    (
                        datetime.now().isoformat(),
                        100 if test_result["success"] else 0,
                        datetime.now().isoformat(),
                        credential_id,
# BRACKET_SURGEON: disabled
#                     ),
# BRACKET_SURGEON: disabled
#                 )
                conn.commit()

                return {
                    "success": test_result["success"],
                    "message": test_result.get("message", "Login test completed"),
                    "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                 }

        except sqlite3.Error as e:
            logger.error(f"Database error during login test: {e}")
            raise HTTPException(status_code=500, detail="Database error")
        except Exception as e:
            logger.error(f"Error during login test: {e}")
            raise HTTPException(status_code=500, detail="Login test failed")


# Service instance
credentials_service = AffiliateCredentialsService()


@router.get("/credentials")
async def get_affiliate_credentials(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """Get all affiliate dashboard credentials"""
    return credentials_service.get_all_credentials()


@router.post("/credentials/{credential_id}/test")
async def test_credential(
    credential_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """Test login for a specific credential"""
    return credentials_service.test_credential_login(credential_id)


@router.get("/credentials/stats")
async def get_credentials_stats(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """Get credential statistics"""
    all_creds = credentials_service.get_all_credentials()
    return all_creds["stats"]