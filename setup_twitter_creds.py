#!/usr/bin/env python3
"""
Script to set up Twitter credentials for the current system
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from secret_store import SecretStore
from integrations.twitter_integration import TwitterIntegration

def setup_twitter_credentials():
    """Set up Twitter credentials interactively"""
    try:
        store = SecretStore()
        
        print("=== Twitter API Configuration ===")
        print("You need to obtain these from https://developer.twitter.com/")
        print("Required credentials:")
        print("1. API Key (Consumer Key)")
        print("2. API Secret (Consumer Secret)")
        print("3. Access Token")
        print("4. Access Token Secret")
        print()
        
        # Check existing credentials
        existing_creds = [
            store.secret_exists('TWITTER_API_KEY'),
            store.secret_exists('TWITTER_API_SECRET'),
            store.secret_exists('TWITTER_ACCESS_TOKEN'),
            store.secret_exists('TWITTER_ACCESS_TOKEN_SECRET')
        ]
        
        if all(existing_creds):
            print("✓ Twitter credentials already configured")
            update = input("Update existing credentials? (y/N): ").lower().startswith('y')
            if not update:
                return test_credentials(store)
        
        # Get credentials from user
        print("\nEnter your Twitter API credentials:")
        api_key = input("Twitter API Key: ").strip()
        api_secret = input("Twitter API Secret: ").strip()
        access_token = input("Twitter Access Token: ").strip()
        access_token_secret = input("Twitter Access Token Secret: ").strip()
        
        if not all([api_key, api_secret, access_token, access_token_secret]):
            print("❌ All Twitter credentials are required")
            return False
        
        # Store credentials
        store.store_secret('TWITTER_API_KEY', api_key)
        store.store_secret('TWITTER_API_SECRET', api_secret)
        store.store_secret('TWITTER_ACCESS_TOKEN', access_token)
        store.store_secret('TWITTER_ACCESS_TOKEN_SECRET', access_token_secret)
        
        print("✅ Twitter credentials stored successfully")
        
        # Test the connection
        return test_credentials(store)
        
    except Exception as e:
        print(f"❌ Error setting up Twitter credentials: {e}")
        return False

def test_credentials(store):
    """Test Twitter credentials"""
    try:
        print("\n🔍 Testing Twitter connection...")
        twitter = TwitterIntegration()
        
        if twitter.test_connection():
            print("✅ Twitter connection successful!")
            return True
        else:
            print("❌ Twitter connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Twitter connection: {e}")
        return False

def check_current_status():
    """Check current Twitter credential status"""
    try:
        store = SecretStore()
        
        credentials = [
            'TWITTER_API_KEY',
            'TWITTER_API_SECRET', 
            'TWITTER_ACCESS_TOKEN',
            'TWITTER_ACCESS_TOKEN_SECRET'
        ]
        
        print("=== Current Twitter Credential Status ===")
        for cred in credentials:
            status = "✅ Set" if store.secret_exists(cred) else "❌ Missing"
            print(f"{cred}: {status}")
        
        all_set = all(store.secret_exists(cred) for cred in credentials)
        print(f"\nOverall Status: {'✅ All credentials configured' if all_set else '❌ Missing credentials'}")
        
        return all_set
        
    except Exception as e:
        print(f"❌ Error checking credential status: {e}")
        return False

if __name__ == "__main__":
    print("Twitter Credential Setup Tool")
    print("============================\n")
    
    # Check current status first
    if check_current_status():
        print("\nTwitter credentials are already configured.")
        setup_new = input("Do you want to update them? (y/N): ").lower().startswith('y')
        if not setup_new:
            print("Exiting...")
            sys.exit(0)
    
    # Set up credentials
    success = setup_twitter_credentials()
    sys.exit(0 if success else 1)