#!/usr/bin/env python3
"""
Weekly Content Generator for The Right Perspective
Generates weekly conservative content specials and fills slow news weeks
"""

import sqlite3
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ContentSegment:
    title: str
    content_type: str  # 'hypocrisy', 'humor', 'analysis', 'compilation'
    description: str
    evidence_urls: List[str]
    talking_points: List[str]
    humor_angle: Optional[str] = None
    estimated_duration: str = "5-7 minutes"

class WeeklyContentGeneratorForRightPerspective:
    def __init__(self, db_path: str = "conservative_research.db"):
        self.db_path = db_path
        
        # Content templates for The Right Perspective
        self.content_templates = {
            'hypocrisy_special': {
                'title_format': "Hypocrisy Alert: {politician} Edition",
                'description': "Exposing the flip-flops and contradictions of Democratic politicians",
                'segments': ['then_vs_now', 'video_evidence', 'impact_analysis', 'humor_commentary']
            },
            'media_lies_compilation': {
                'title_format': "Media Lies Weekly: {topic} Edition", 
                'description': "Breaking down mainstream media falsehoods and bias",
                'segments': ['false_predictions', 'narrative_shifts', 'fact_checks', 'conservative_response']
            },
            'policy_flip_flop': {
                'title_format': "The Great {policy} Flip-Flop",
                'description': "How Democrats completely reversed their positions for political gain",
                'segments': ['historical_position', 'the_flip', 'excuses_made', 'real_impact']
            },
            'slow_news_special': {
                'title_format': "Greatest Hits: {theme} Hypocrisy",
                'description': "Classic examples of Democratic contradictions and lies",
                'segments': ['hall_of_shame', 'evergreen_examples', 'pattern_analysis', 'lessons_learned']
            }
        }
        
        # Humor styles inspired by conservative hosts
        self.humor_styles = {
            'gutfeld_style': {
                'approach': 'Late-night comedy with political edge',
                'techniques': ['absurdist observations', 'pop culture references', 'panel banter'],
                'tone': 'Sarcastic but not mean-spirited'
            },
            'watters_style': {
                'approach': 'Investigative with comedic elements',
                'techniques': ['man-on-street reactions', 'visual comparisons', 'deadpan delivery'],
                'tone': 'Confident and slightly mocking'
            },
            'crowder_style': {
                'approach': 'Sketch comedy meets political commentary',
                'techniques': ['character impressions', 'visual gags', 'audience interaction'],
                'tone': 'Energetic and provocative'
            },
            'bongino_style': {
                'approach': 'Passionate analysis with humor breaks',
                'techniques': ['righteous indignation', 'catchphrases', 'audience callbacks'],
                'tone': 'Intense but relatable'
            }
        }
        
        # Weekly themes for content rotation
        self.weekly_themes = {
            'monday': 'Media Lies Monday',
            'tuesday': 'Flip-Flop Tuesday', 
            'wednesday': 'Hypocrisy Hump Day',
            'thursday': 'Throwback Thursday (Classic Lies)',
            'friday': 'Fact-Check Friday',
            'saturday': 'Saturday Satire',
            'sunday': 'Sunday Summary'
        }
    
    def get_recent_hypocrisy_examples(self, days_back: int = 30, limit: int = 10) -> List[Dict]:
        """Get recent hypocrisy examples from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        cursor.execute('''
            SELECT politician_name, example_title, description, evidence_url, 
                   category, impact_level, created_at
            FROM hypocrisy_examples 
            WHERE created_at >= ? AND evidence_url IS NOT NULL
            ORDER BY impact_level DESC, created_at DESC
            LIMIT ?
        ''', (cutoff_date, limit))
        
        examples = []
        for row in cursor.fetchall():
            examples.append({
                'politician': row[0],
                'title': row[1],
                'description': row[2],
                'evidence_url': row[3],
                'category': row[4],
                'impact_level': row[5],
                'date': row[6]
            })
        
        conn.close()
        return examples
    
    def get_evergreen_content(self, category: str = None, limit: int = 5) -> List[Dict]:
        """Get evergreen hypocrisy examples for slow news periods"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if category:
            cursor.execute('''
                SELECT politician_name, example_title, description, evidence_url, 
                       category, impact_level
                FROM hypocrisy_examples 
                WHERE category = ? AND impact_level >= 8
                ORDER BY impact_level DESC
                LIMIT ?
            ''', (category, limit))
        else:
            cursor.execute('''
                SELECT politician_name, example_title, description, evidence_url, 
                       category, impact_level
                FROM hypocrisy_examples 
                WHERE impact_level >= 8
                ORDER BY impact_level DESC
                LIMIT ?
            ''', (limit,))
        
        examples = []
        for row in cursor.fetchall():
            examples.append({
                'politician': row[0],
                'title': row[1],
                'description': row[2],
                'evidence_url': row[3],
                'category': row[4],
                'impact_level': row[5]
            })
        
        conn.close()
        return examples
    
    def get_trending_topics(self) -> List[Dict]:
        """Get trending topics from recent news scraping"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get recent high-relevance articles
        cursor.execute('''
            SELECT title, source, relevance_score, url, scraped_at
            FROM scraped_articles 
            WHERE right_perspective_potential = TRUE 
                AND scraped_at >= datetime('now', '-7 days')
            ORDER BY relevance_score DESC
            LIMIT 10
        ''')
        
        trending = []
        for row in cursor.fetchall():
            trending.append({
                'title': row[0],
                'source': row[1],
                'relevance_score': row[2],
                'url': row[3],
                'date': row[4]
            })
        
        conn.close()
        return trending
    
    def generate_humor_angle(self, topic: str, style: str = 'gutfeld_style') -> str:
        """Generate humor angle for content based on conservative host styles"""
        style_config = self.humor_styles.get(style, self.humor_styles['gutfeld_style'])
        
        humor_templates = {
            'gutfeld_style': [
                f"You know what's funnier than {topic}? The fact that Democrats think we forgot their old position!",
                f"If {topic} was a movie, it would be called 'The Incredible Flip-Flopping Democrat'",
                f"Breaking: Local Democrat discovers {topic} is popular, immediately changes 20-year position"
            ],
            'watters_style': [
                f"So I went out and asked people about {topic}. You won't believe what happened next...",
                f"Here's a side-by-side comparison that will make you question everything about {topic}",
                f"The {topic} files: What they don't want you to see"
            ],
            'crowder_style': [
                f"Change My Mind: Democrats are consistent on {topic} (IMPOSSIBLE CHALLENGE)",
                f"I dressed up as a {topic} supporter and infiltrated a Democratic meeting",
                f"BREAKING: We found the exact moment Democrats flip-flopped on {topic}"
            ],
            'bongino_style': [
                f"Folks, the {topic} situation is INSANE and I'm going to break it down for you",
                f"Remember the names! These are the Democrats who lied about {topic}",
                f"The {topic} scandal that the media won't cover - but we will!"
            ]
        }
        
        templates = humor_templates.get(style, humor_templates['gutfeld_style'])
        return random.choice(templates)
    
    def create_hypocrisy_special(self, politician: str = None) -> Dict:
        """Create a hypocrisy special episode"""
        if not politician:
            # Get most hypocritical politician from recent data
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT politician_name, COUNT(*) as hypocrisy_count
                FROM hypocrisy_examples 
                WHERE created_at >= datetime('now', '-30 days')
                GROUP BY politician_name
                ORDER BY hypocrisy_count DESC
                LIMIT 1
            ''')
            result = cursor.fetchone()
            politician = result[0] if result else "Nancy Pelosi"
            conn.close()
        
        # Get examples for this politician
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT example_title, description, evidence_url, category
            FROM hypocrisy_examples 
            WHERE politician_name = ?
            ORDER BY impact_level DESC
            LIMIT 5
        ''', (politician,))
        
        examples = cursor.fetchall()
        conn.close()
        
        segments = []
        
        # Opening segment
        segments.append(ContentSegment(
            title=f"Welcome to Hypocrisy Alert: {politician} Edition",
            content_type="introduction",
            description=f"Setting up the {politician} hypocrisy showcase",
            evidence_urls=[],
            talking_points=[
                f"Today we're focusing on {politician}",
                "Get ready for some serious flip-flopping",
                "We have the receipts!"
            ],
            humor_angle=self.generate_humor_angle(politician, 'gutfeld_style')
        ))
        
        # Main examples
        for i, example in enumerate(examples[:3]):
            segments.append(ContentSegment(
                title=f"Hypocrisy #{i+1}: {example[0]}",
                content_type="hypocrisy",
                description=example[1],
                evidence_urls=[example[2]] if example[2] else [],
                talking_points=[
                    "Show the before and after",
                    "Explain the political motivation",
                    "Highlight the absurdity"
                ],
                humor_angle=self.generate_humor_angle(example[3], 'watters_style')
            ))
        
        # Closing segment
        segments.append(ContentSegment(
            title="The Pattern of Hypocrisy",
            content_type="analysis",
            description="Connecting the dots on Democratic flip-flopping",
            evidence_urls=[],
            talking_points=[
                "This isn't isolated - it's a pattern",
                "Why do they think we won't notice?",
                "What this means for voters"
            ],
            humor_angle="Remember folks, consistency is apparently not a Democratic value!"
        ))
        
        return {
            'episode_title': f"Hypocrisy Alert: {politician} Edition",
            'episode_type': 'hypocrisy_special',
            'target_politician': politician,
            'estimated_length': '20-25 minutes',
            'segments': segments,
            'cross_promotion': {
                'can_promote_others': True,
                'others_promote_this': False,
                'neutral_channels_only': True
            }
        }
    
    def create_slow_news_special(self) -> Dict:
        """Create content for slow news weeks using evergreen examples"""
        themes = ['Border Security', 'Economic Policy', 'Foreign Policy', 'Healthcare', 'Energy Policy']
        selected_theme = random.choice(themes)
        
        evergreen_examples = self.get_evergreen_content(selected_theme.lower().replace(' ', '_'), 5)
        
        segments = []
        
        # Opening
        segments.append(ContentSegment(
            title=f"Greatest Hits: {selected_theme} Hypocrisy Hall of Fame",
            content_type="introduction",
            description="Classic examples of Democratic flip-flopping that never get old",
            evidence_urls=[],
            talking_points=[
                "Slow news week? Perfect time for classics!",
                f"Let's revisit the greatest {selected_theme} flip-flops",
                "These never stop being relevant"
            ],
            humor_angle=f"Think of this as the 'Greatest Hits' album of {selected_theme} hypocrisy!"
        ))
        
        # Classic examples
        for i, example in enumerate(evergreen_examples):
            segments.append(ContentSegment(
                title=f"Classic #{i+1}: {example['title']}",
                content_type="compilation",
                description=example['description'],
                evidence_urls=[example['evidence_url']] if example['evidence_url'] else [],
                talking_points=[
                    "Why this example is timeless",
                    "The political calculation behind the flip",
                    "How it impacts current policy"
                ],
                humor_angle=self.generate_humor_angle(example['title'], 'crowder_style')
            ))
        
        # Pattern analysis
        segments.append(ContentSegment(
            title="The Playbook Revealed",
            content_type="analysis",
            description="Understanding the Democratic flip-flop playbook",
            evidence_urls=[],
            talking_points=[
                "Step 1: Take a strong position",
                "Step 2: Wait for political winds to change", 
                "Step 3: Flip and pretend you never changed",
                "Step 4: Attack anyone who remembers"
            ],
            humor_angle="It's like they have a manual: 'How to Flip-Flop Without Shame'"
        ))
        
        return {
            'episode_title': f"Greatest Hits: {selected_theme} Hypocrisy Hall of Fame",
            'episode_type': 'slow_news_special',
            'theme': selected_theme,
            'estimated_length': '15-20 minutes',
            'segments': segments,
            'cross_promotion': {
                'can_promote_others': True,
                'others_promote_this': False,
                'neutral_channels_only': True
            }
        }
    
    def create_weekly_content_plan(self) -> Dict:
        """Create a full week's content plan for The Right Perspective"""
        # Check if there's enough recent news
        recent_examples = self.get_recent_hypocrisy_examples(7, 5)
        trending_topics = self.get_trending_topics()
        
        weekly_plan = {
            'week_of': datetime.now().strftime('%Y-%m-%d'),
            'content_strategy': 'recent_news' if len(recent_examples) >= 3 else 'evergreen_focus',
            'episodes': []
        }
        
        if len(recent_examples) >= 3:
            # Enough recent content for news-based episodes
            weekly_plan['episodes'].append(self.create_hypocrisy_special())
            
            # Add trending topic episode
            if trending_topics:
                weekly_plan['episodes'].append({
                    'episode_title': f"Breaking: {trending_topics[0]['title'][:50]}...",
                    'episode_type': 'trending_analysis',
                    'source_article': trending_topics[0],
                    'estimated_length': '10-15 minutes'
                })
        else:
            # Slow news week - use evergreen content
            weekly_plan['episodes'].append(self.create_slow_news_special())
            
            # Add a "Best Of" compilation
            weekly_plan['episodes'].append({
                'episode_title': "Best Of: Democratic Lies That Aged Like Milk",
                'episode_type': 'compilation',
                'estimated_length': '12-18 minutes'
            })
        
        return weekly_plan
    
    def save_content_plan(self, content_plan: Dict) -> int:
        """Save weekly content plan to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weekly_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_of DATE NOT NULL,
                content_strategy TEXT NOT NULL,
                plan_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'planned'
            )
        ''')
        
        cursor.execute('''
            INSERT INTO weekly_content (week_of, content_strategy, plan_data)
            VALUES (?, ?, ?)
        ''', (
            content_plan['week_of'],
            content_plan['content_strategy'],
            json.dumps(content_plan)
        ))
        
        plan_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Saved weekly content plan {plan_id} for week of {content_plan['week_of']}")
        return plan_id
    
    def generate_cross_promotion_strategy(self) -> Dict:
        """Generate cross-promotion strategy for The Right Perspective"""
        return {
            'promotion_rules': {
                'the_right_perspective_can_promote': [
                    'Other conservative channels',
                    'Politically neutral gaming channels',
                    'Educational content creators',
                    'Independent journalists'
                ],
                'others_cannot_promote_trp': True,
                'reason': 'Maintain political neutrality of other channels'
            },
            'promotion_opportunities': [
                'End-of-episode shoutouts to similar content',
                'Collaboration with gaming conservatives',
                'Guest appearances on neutral shows',
                'Cross-reference to educational content'
            ],
            'content_sharing': {
                'trp_shares_clips': 'Yes, with attribution',
                'others_share_trp_clips': 'No, to maintain neutrality',
                'exception': 'Factual information can be shared without political context'
            }
        }

def main():
    """Main function for weekly content generation"""
    generator = WeeklyContentGeneratorForRightPerspective()
    
    print("📅 Generating weekly content for The Right Perspective...")
    
    # Create weekly content plan
    weekly_plan = generator.create_weekly_content_plan()
    
    print(f"\n📺 Weekly Content Plan for {weekly_plan['week_of']}:")
    print(f"Strategy: {weekly_plan['content_strategy']}")
    
    for i, episode in enumerate(weekly_plan['episodes'], 1):
        print(f"\nEpisode {i}: {episode['episode_title']}")
        print(f"Type: {episode['episode_type']}")
        print(f"Length: {episode['estimated_length']}")
        
        if 'segments' in episode:
            print(f"Segments: {len(episode['segments'])}")
            for j, segment in enumerate(episode['segments'][:3], 1):
                print(f"  {j}. {segment.title} ({segment.content_type})")
    
    # Save the plan
    plan_id = generator.save_content_plan(weekly_plan)
    print(f"\n💾 Content plan saved with ID: {plan_id}")
    
    # Generate cross-promotion strategy
    cross_promo = generator.generate_cross_promotion_strategy()
    print(f"\n🤝 Cross-Promotion Strategy:")
    print(f"TRP can promote: {', '.join(cross_promo['promotion_rules']['the_right_perspective_can_promote'])}")
    print(f"Others promote TRP: {'No' if cross_promo['promotion_rules']['others_cannot_promote_trp'] else 'Yes'}")
    print(f"Reason: {cross_promo['promotion_rules']['reason']}")

if __name__ == "__main__":
    main()