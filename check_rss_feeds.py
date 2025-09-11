#!/usr/bin/env python3
import sqlite3

def check_rss_feeds():
    """Check RSS feeds status for all channels"""
    try:
        conn = sqlite3.connect('data/right_perspective.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT channel_id, feed_url, status, last_checked, error_count 
            FROM channel_rss_feeds 
            ORDER BY channel_id
        ''')
        
        rows = cursor.fetchall()
        print('\n📡 RSS Feeds Status:')
        print(f'Total Feeds: {len(rows)}')
        
        current_channel = ''
        for row in rows:
            if row[0] != current_channel:
                print(f'\n{row[0]}:')
                current_channel = row[0]
            
            status_icon = '✅' if row[2] == 'active' else '❌'
            print(f'  {status_icon} {row[1]}')
            print(f'     Status: {row[2]}, Last Check: {row[3]}, Errors: {row[4]}')
        
        conn.close()
        
    except Exception as e:
        print(f'Error checking RSS feeds: {e}')

if __name__ == '__main__':
    check_rss_feeds()