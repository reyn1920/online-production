#!/usr/bin/env python3
"""
🔐 Secure Credential Generator

Generates cryptographically secure passwords and API keys for production deployment.
Follows security best practices with appropriate entropy and character sets.

Usage:
    python scripts/generate_credentials.py
    python scripts/generate_credentials.py --format github
    python scripts/generate_credentials.py --format netlify
"""

import secrets
import string
import argparse
import json
from typing import Dict, Any


class CredentialGenerator:
    """Generates secure credentials for production deployment."""
    
    def __init__(self):
        self.credentials = {}
        
    def generate_password(self, length: int = 16, include_symbols: bool = True) -> str:
        """Generate a secure password with specified length and character set."""
        chars = string.ascii_letters + string.digits
        if include_symbols:
            chars += '!@#$%^&*()_+-=[]{}|;:,.<>?'
        
        return ''.join(secrets.choice(chars) for _ in range(length))
    
    def generate_api_key(self, prefix: str = "trae", length: int = 32) -> str:
        """Generate a secure API key with prefix."""
        key_part = secrets.token_hex(length)
        return f"{prefix}-{key_part}"
    
    def generate_secret_key(self, length: int = 64) -> str:
        """Generate a URL-safe secret key."""
        return secrets.token_urlsafe(length)
    
    def generate_all_credentials(self) -> Dict[str, Any]:
        """Generate all required credentials for production."""
        
        print("🔐 Generating secure credentials...\n")
        
        # Critical Security Variables
        self.credentials.update({
            'ADMIN_PASSWORD': self.generate_password(16, True),
            'CONFIG_MASTER_PASSWORD': self.generate_secret_key(32),
            'GRAFANA_ADMIN_PASSWORD': self.generate_password(16, True),
            'POSTGRES_PASSWORD': self.generate_password(20, True),
            'MASTER_API_KEY': self.generate_api_key('trae-master', 32),
            'FLASK_SECRET_KEY': self.generate_secret_key(64),
        })
        
        # Additional Security Keys
        self.credentials.update({
            'JWT_SECRET_KEY': self.generate_secret_key(64),
            'ENCRYPTION_KEY': self.generate_secret_key(32),
            'SESSION_SECRET': self.generate_secret_key(32),
        })
        
        return self.credentials
    
    def print_credentials(self, format_type: str = 'env'):
        """Print credentials in specified format."""
        
        if format_type == 'github':
            self._print_github_format()
        elif format_type == 'netlify':
            self._print_netlify_format()
        elif format_type == 'json':
            self._print_json_format()
        else:
            self._print_env_format()
    
    def _print_env_format(self):
        """Print in .env file format."""
        print("📄 Environment Variables (.env format):")
        print("=" * 50)
        for key, value in self.credentials.items():
            print(f"{key}={value}")
        print("\n⚠️  IMPORTANT: Add these to your .env.production file")
        print("⚠️  NEVER commit .env.production to version control!")
    
    def _print_github_format(self):
        """Print GitHub Secrets setup instructions."""
        print("🐙 GitHub Secrets Setup:")
        print("=" * 50)
        print("Add these secrets to your GitHub repository:")
        print("Repository → Settings → Secrets and variables → Actions → New repository secret\n")
        
        for key, value in self.credentials.items():
            print(f"Name: {key}")
            print(f"Value: {value}")
            print("-" * 30)
    
    def _print_netlify_format(self):
        """Print Netlify Environment Variables setup instructions."""
        print("🌐 Netlify Environment Variables Setup:")
        print("=" * 50)
        print("Add these to your Netlify site:")
        print("Site settings → Environment variables → Add a variable\n")
        
        # Only include client-safe variables for Netlify
        client_safe = {
            'MASTER_API_KEY': self.credentials['MASTER_API_KEY'],
            'FLASK_SECRET_KEY': self.credentials['FLASK_SECRET_KEY'],
        }
        
        for key, value in client_safe.items():
            print(f"Key: {key}")
            print(f"Value: {value}")
            print("Scopes: All deploy contexts")
            print("⚠️  Mark as SECRET in Netlify UI")
            print("-" * 30)
    
    def _print_json_format(self):
        """Print in JSON format for programmatic use."""
        print(json.dumps(self.credentials, indent=2))
    
    def save_to_file(self, filename: str = '.env.production.generated'):
        """Save credentials to a file."""
        with open(filename, 'w') as f:
            f.write("# 🔐 Generated Production Credentials\n")
            f.write("# Generated on: $(date)\n")
            f.write("# NEVER commit this file to version control!\n\n")
            
            for key, value in self.credentials.items():
                f.write(f"{key}={value}\n")
        
        print(f"\n💾 Credentials saved to: {filename}")
        print("⚠️  Remember to add this file to .gitignore!")


def main():
    parser = argparse.ArgumentParser(description='Generate secure credentials for production')
    parser.add_argument('--format', choices=['env', 'github', 'netlify', 'json'], 
                       default='env', help='Output format')
    parser.add_argument('--save', action='store_true', 
                       help='Save credentials to .env.production.generated')
    parser.add_argument('--quiet', action='store_true', 
                       help='Suppress informational messages')
    
    args = parser.parse_args()
    
    generator = CredentialGenerator()
    generator.generate_all_credentials()
    
    if not args.quiet:
        print("✅ All credentials generated successfully!\n")
    
    generator.print_credentials(args.format)
    
    if args.save:
        generator.save_to_file()
    
    if not args.quiet:
        print("\n🔒 Security Reminders:")
        print("1. Store these credentials securely")
        print("2. Never commit them to version control")
        print("3. Rotate credentials quarterly")
        print("4. Use different credentials for each environment")
        print("5. Monitor for credential exposure in logs")


if __name__ == '__main__':
    main()