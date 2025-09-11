#!/usr/bin/env python3

from backend.secret_store import SecretStore

def check_youtube_credentials():
    """Check YouTube credentials in secret store"""
    try:
        store = SecretStore()
        youtube_creds = [
            'YOUTUBE_CLIENT_ID',
            'YOUTUBE_CLIENT_SECRET', 
            'YOUTUBE_REFRESH_TOKEN',
            'YOUTUBE_ACCESS_TOKEN'
        ]
        
        print('\n🔐 YouTube Credentials Status:')
        print('=' * 40)
        
        missing_creds = []
        for cred in youtube_creds:
            value = store.get_secret(cred)
            status = 'SET' if value else 'MISSING'
            icon = '✅' if value else '❌'
            print(f'  {icon} {cred}: {status}')
            if not value:
                missing_creds.append(cred)
        
        print('\n📊 Summary:')
        print(f'  Total credentials: {len(youtube_creds)}')
        print(f'  Configured: {len(youtube_creds) - len(missing_creds)}')
        print(f'  Missing: {len(missing_creds)}')
        
        if missing_creds:
            print('\n⚠️  Missing credentials:')
            for cred in missing_creds:
                print(f'    - {cred}')
            print('\n💡 To fix: Configure missing credentials in the secret store')
        else:
            print('\n✅ All YouTube credentials are configured!')
            
    except Exception as e:
        print(f'❌ Error checking credentials: {e}')

if __name__ == '__main__':
    check_youtube_credentials()