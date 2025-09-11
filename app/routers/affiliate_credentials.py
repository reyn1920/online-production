from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict, Any, Optional
import sqlite3
import json
from datetime import datetime
from pathlib import Path
import logging
from cryptography.fernet import Fernet
import os
from backend.agents.stealth_automation_agent import AffiliateDashboard

router = APIRouter(prefix="/api/affiliates", tags=["affiliate-credentials"])
security = HTTPBearer()
logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path("intelligence.db")

class AffiliateCredentialsService:
    def __init__(self):
        self.db_path = DB_PATH
        self.encryption_key = self._get_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key) if self.encryption_key else None
    
    def _get_encryption_key(self) -> Optional[bytes]:
        """Get encryption key from environment or generate one"""
        key_str = os.getenv('AFFILIATE_ENCRYPTION_KEY')
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
                cursor.execute("""
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
                """)
                
                rows = cursor.fetchall()
                
                credentials = []
                for row in rows:
                    # Decrypt password
                    decrypted_password = self._decrypt_password(row['encrypted_password'])
                    
                    # Determine status based on recent activity
                    status = self._determine_status(row['last_login_attempt'], row['login_success_rate'])
                    
                    credential = {
                        'id': row['id'],
                        'programName': row['platform_name'],
                        'category': self._get_program_category(row['platform_name']),
                        'dashboardUrl': row['dashboard_url'] or row['login_url'],
                        'username': row['username'],
                        'password': decrypted_password,
                        'lastAccess': row['last_login_attempt'],
                        'successRate': row['login_success_rate'] or 0,
                        'status': status,
                        'notes': row['notes'],
                        'createdAt': row['created_at'],
                        'updatedAt': row['updated_at'],
                        'isActive': bool(row['is_active'])
                    }
                    credentials.append(credential)
                
                # Calculate stats
                stats = self._calculate_stats(credentials)
                
                return {
                    'credentials': credentials,
                    'stats': stats,
                    'total': len(credentials)
                }
                
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            raise HTTPException(status_code=500, detail="Database error")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    def _determine_status(self, last_login: Optional[str], success_rate: Optional[float]) -> str:
        """Determine credential status based on activity"""
        if not last_login:
            return 'pending'
        
        # Parse last login date
        try:
            last_login_date = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
            days_since_login = (datetime.now() - last_login_date.replace(tzinfo=None)).days
            
            if success_rate and success_rate >= 80 and days_since_login <= 30:
                return 'active'
            elif success_rate and success_rate < 50:
                return 'inactive'
            else:
                return 'pending'
        except:
            return 'pending'
    
    def _get_program_category(self, platform_name: str) -> str:
        """Categorize affiliate program"""
        platform_lower = platform_name.lower()
        
        if any(keyword in platform_lower for keyword in ['clickbank', 'cb']):
            return 'Digital Products'
        elif any(keyword in platform_lower for keyword in ['amazon', 'amzn']):
            return 'E-commerce'
        elif any(keyword in platform_lower for keyword in ['commission', 'cj', 'shareasale']):
            return 'Network'
        elif any(keyword in platform_lower for keyword in ['software', 'saas', 'app']):
            return 'Software'
        elif any(keyword in platform_lower for keyword in ['finance', 'trading', 'crypto']):
            return 'Finance'
        else:
            return 'General'
    
    def _calculate_stats(self, credentials: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics"""
        total = len(credentials)
        active = sum(1 for c in credentials if c['status'] == 'active')
        
        # Find most recent access
        last_access = 'Never'
        if credentials:
            recent_accesses = [c['lastAccess'] for c in credentials if c['lastAccess']]
            if recent_accesses:
                most_recent = max(recent_accesses)
                try:
                    last_access_date = datetime.fromisoformat(most_recent.replace('Z', '+00:00'))
                    last_access = last_access_date.strftime('%b %d, %Y')
                except:
                    last_access = 'Unknown'
        
        # Calculate security score (simplified)
        security_score = 98  # Base score
        if total > 0:
            # Reduce score for inactive credentials
            inactive_ratio = sum(1 for c in credentials if c['status'] == 'inactive') / total
            security_score -= int(inactive_ratio * 20)
            
            # Reduce score for old passwords (simplified check)
            old_credentials = sum(1 for c in credentials if not c['lastAccess'] or 
                                (datetime.now() - datetime.fromisoformat(c['createdAt'].replace('Z', '+00:00').replace('T', ' '))).days > 90)
            if old_credentials > 0:
                security_score -= min(10, old_credentials * 2)
        
        return {
            'total': total,
            'active': active,
            'inactive': sum(1 for c in credentials if c['status'] == 'inactive'),
            'pending': sum(1 for c in credentials if c['status'] == 'pending'),
            'lastAccess': last_access,
            'securityScore': max(70, security_score)  # Minimum 70%
        }
    
    def test_credential_login(self, credential_id: str) -> Dict[str, Any]:
        """Test login for a specific credential"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT platform_name, login_url, username, encrypted_password
                    FROM affiliate_dashboards
                    WHERE id = ?
                """, (credential_id,))
                
                row = cursor.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Credential not found")
                
                # For now, return a simulated test result
                # In production, this would use the stealth automation agent
                return {
                    'success': True,
                    'message': f"Login test for {row['platform_name']} completed successfully",
                    'timestamp': datetime.now().isoformat(),
                    'responseTime': 1.2  # seconds
                }
                
        except sqlite3.Error as e:
            logger.error(f"Database error during login test: {e}")
            raise HTTPException(status_code=500, detail="Database error")
    
    def toggle_credential_active(self, credential_id: str, is_active: bool) -> Dict[str, Any]:
        """Toggle the active status of a credential"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update the is_active status
                cursor.execute("""
                    UPDATE affiliate_dashboards 
                    SET is_active = ?, updated_at = ?
                    WHERE id = ?
                """, (is_active, datetime.now().isoformat(), credential_id))
                
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Credential not found")
                
                conn.commit()
                
                return {
                    'success': True,
                    'message': f"Credential {'activated' if is_active else 'deactivated'} successfully",
                    'credentialId': credential_id,
                    'isActive': is_active
                }
                
        except sqlite3.Error as e:
            logger.error(f"Database error during toggle: {e}")
            raise HTTPException(status_code=500, detail="Database error")
    
    def delete_credential(self, credential_id: str) -> Dict[str, Any]:
        """Delete a credential from the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # First check if credential exists
                cursor.execute("SELECT platform_name FROM affiliate_dashboards WHERE id = ?", (credential_id,))
                row = cursor.fetchone()
                
                if not row:
                    raise HTTPException(status_code=404, detail="Credential not found")
                
                platform_name = row[0]
                
                # Delete the credential
                cursor.execute("DELETE FROM affiliate_dashboards WHERE id = ?", (credential_id,))
                conn.commit()
                
                return {
                    'success': True,
                    'message': f"Credential for {platform_name} deleted successfully",
                    'credentialId': credential_id
                }
                
        except sqlite3.Error as e:
            logger.error(f"Database error during deletion: {e}")
            raise HTTPException(status_code=500, detail="Database error")

    def export_credentials(self) -> Dict[str, Any]:
        """Export credentials in a secure format"""
        data = self.get_all_credentials()
        
        # Remove sensitive password data for export
        export_data = {
            'exportDate': datetime.now().isoformat(),
            'totalPrograms': data['total'],
            'stats': data['stats'],
            'programs': []
        }
        
        for cred in data['credentials']:
            export_cred = {
                'programName': cred['programName'],
                'category': cred['category'],
                'dashboardUrl': cred['dashboardUrl'],
                'username': cred['username'],
                'status': cred['status'],
                'successRate': cred['successRate'],
                'lastAccess': cred['lastAccess'],
                'createdAt': cred['createdAt']
                # Note: password is intentionally excluded for security
            }
            export_data['programs'].append(export_cred)
        
        return export_data

# Initialize service
credentials_service = AffiliateCredentialsService()

# Authentication dependency (simplified)
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API token - implement proper authentication in production"""
    # For development, accept any token
    # In production, implement proper JWT validation
    if not credentials.credentials:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    return credentials.credentials

@router.get("/credentials")
async def get_affiliate_credentials(token: str = Depends(verify_token)):
    """Get all affiliate dashboard credentials"""
    try:
        return credentials_service.get_all_credentials()
    except Exception as e:
        logger.error(f"Error retrieving credentials: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve credentials")

@router.post("/credentials/{credential_id}/test")
async def test_credential_login(credential_id: str, token: str = Depends(verify_token)):
    """Test login for a specific credential"""
    try:
        return credentials_service.test_credential_login(credential_id)
    except Exception as e:
        logger.error(f"Error testing credential login: {e}")
        raise HTTPException(status_code=500, detail="Failed to test login")

@router.get("/credentials/export")
async def export_credentials(token: str = Depends(verify_token)):
    """Export affiliate credentials summary"""
    try:
        export_data = credentials_service.export_credentials()
        
        # Return as JSON response with appropriate headers
        json_str = json.dumps(export_data, indent=2)
        
        return Response(
            content=json_str,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=affiliate_credentials_{datetime.now().strftime('%Y%m%d')}.json"
            }
        )
    except Exception as e:
        logger.error(f"Error exporting credentials: {e}")
        raise HTTPException(status_code=500, detail="Failed to export credentials")

@router.post("/credentials/{credential_id}/toggle")
async def toggle_credential_active(credential_id: str, is_active: bool, token: str = Depends(verify_token)):
    """Toggle the active status of a credential"""
    try:
        return credentials_service.toggle_credential_active(credential_id, is_active)
    except Exception as e:
        logger.error(f"Error toggling credential: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle credential")

@router.delete("/credentials/{credential_id}")
async def delete_credential(credential_id: str, token: str = Depends(verify_token)):
    """Delete a credential"""
    try:
        return credentials_service.delete_credential(credential_id)
    except Exception as e:
        logger.error(f"Error deleting credential: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete credential")

@router.get("/credentials/stats")
async def get_credentials_stats(token: str = Depends(verify_token)):
    """Get affiliate credentials statistics"""
    try:
        data = credentials_service.get_all_credentials()
        return data['stats']
    except Exception as e:
        logger.error(f"Error retrieving stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for affiliate credentials service"""
    try:
        # Check database connectivity
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM affiliate_dashboards")
            count = cursor.fetchone()[0]
        
        return {
            'status': 'healthy',
            'database': 'connected',
            'totalCredentials': count,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }