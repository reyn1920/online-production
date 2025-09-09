#!/usr/bin/env python3
"""
Mock Secret Store for testing without cryptography dependency
"""

import os
import json
from typing import Optional, Dict, Any

class MockSecretStore:
    """Mock implementation of SecretStore for testing purposes"""
    
    def __init__(self, db_path: str = "mock_secrets.json"):
        self.db_path = db_path
        self._secrets = {}
        self._load_secrets()
    
    def _load_secrets(self):
        """Load secrets from file or create empty store"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r') as f:
                    self._secrets = json.load(f)
            except Exception:
                self._secrets = {}
        else:
            self._secrets = {}
    
    def _save_secrets(self):
        """Save secrets to file"""
        try:
            with open(self.db_path, 'w') as f:
                json.dump(self._secrets, f, indent=2)
        except Exception:
            pass
    
    def store_secret(self, key: str, value: str) -> bool:
        """Store a secret (mock implementation)"""
        self._secrets[key] = value
        self._save_secrets()
        return True
    
    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve a secret (mock implementation)"""
        return self._secrets.get(key)
    
    def delete_secret(self, key: str) -> bool:
        """Delete a secret (mock implementation)"""
        if key in self._secrets:
            del self._secrets[key]
            self._save_secrets()
            return True
        return False
    
    def list_secrets(self) -> list:
        """List all secret keys"""
        return list(self._secrets.keys())
    
    def secret_exists(self, key: str) -> bool:
        """Check if a secret exists"""
        return key in self._secrets

# Create a global instance for compatibility
SecretStore = MockSecretStore