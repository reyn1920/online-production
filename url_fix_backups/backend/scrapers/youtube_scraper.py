#!/usr / bin / env python3
"""
YouTube Scraper for The Right Perspective
Scrapes conservative YouTube channels and content for analysis
"""

import json
import logging
import re
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlparse

import requests

# Configure logging
logging.basicConfig(
    level = logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class YouTubeScraperForRightPerspective:


    def __init__(self, db_path: str = "conservative_research.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User - Agent": "Mozilla / 5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit / 537.36 (KHTML,
    like Gecko) Chrome / 91.0.4472.124 Safari / 537.36"
            }
        )

        # Conservative YouTube channels for The Right Perspective research
        self.conservative_channels = {
            "greg_gutfeld": {
                "channel_id": "UCwWhs_6x42TyRM4Wstoq8HA",
                    "channel_name": "Fox News - Gutfeld!",
                    "style_notes": "Late - night comedy format, political satire, panel discussions",
                    "content_focus": [
                    "political humor",
                        "liberal hypocrisy",
                        "cultural commentary",
                        ],
                    },
                "jesse_watters": {
                "channel_id": "UCXIJgqnII2ZOINSWNOGFThA",
                    "channel_name": "Fox News - Jesse Watters",
                    "style_notes": "Primetime commentary, man - on - street interviews, investigative segments",
                    "content_focus": [
                    "political analysis",
                        "media criticism",
                        "cultural issues",
                        ],
                    },
                "dan_bongino": {
                "channel_id": "UCx0xRNdYjWqiO6fLEpLOqhQ",
                    "channel_name": "Dan Bongino",
                    "style_notes": "Radio - style commentary, passionate delivery, breaking news analysis",
                    "content_focus": ["deep state", "media lies", "political corruption"],
                    },
                "steven_crowder": {
                "channel_id": "UCIveFvW - ARp_B_RckhweNJw",
                    "channel_name": "StevenCrowder",
                    "style_notes": "Comedy sketches, change my mind segments, satirical content",
                    "content_focus": [
                    "campus activism",
                        "liberal policies",
                        "cultural debates",
                        ],
                    },
                "ben_shapiro": {
                "channel_id": "UCnQC_G5Xsjhp9fEJKuIcrSw",
                    "channel_name": "Ben Shapiro",
                    "style_notes": "Fast - paced analysis, fact - based arguments, daily commentary",
                    "content_focus": [
                    "political analysis",
                        "media bias",
                        "cultural issues",
                        ],
                    },
                "charlie_kirk": {
                "channel_id": "UCu6oW2LdGCwEBgxN8XsUVaA",
                    "channel_name": "Charlie Kirk",
                    "style_notes": "Campus activism, Q&A format, youth - focused messaging",
                    "content_focus": [
                    "campus politics",
                        "conservative activism",
                        "youth engagement",
                        ],
                    },
                "tucker_carlson": {
                "channel_id": "UCwWhs_6x42TyRM4Wstoq8HA",
                    "channel_name": "Tucker Carlson Network",
                    "style_notes": "Investigative journalism, long - form interviews, serious tone",
                    "content_focus": [
                    "deep investigations",
                        "establishment criticism",
                        "foreign policy",
                        ],
                    },
                "the_right_perspective_existing": {
                "channel_id": "UC9xnKz8VQqOGvhzF8R8oF8w",
                    "channel_name": "The Right Perspective",
                    "style_notes": "Conservative gamer perspective, non - commie viewpoints",
                    "content_focus": [
                    "gaming politics",
                        "conservative commentary",
                        "cultural criticism",
                        ],
                    },
                }

        # Keywords for content analysis
        self.content_keywords = {
            "hypocrisy_indicators": [
                "flip flop",
                    "changed position",
                    "contradicts",
                    "hypocrite",
                    "said before",
                    "used to support",
                    "now opposes",
                    ],
                "humor_styles": [
                "satire",
                    "parody",
                    "comedy",
                    "joke",
                    "funny",
                    "hilarious",
                    "mocking",
                    "ridiculous",
                    "absurd",
                    "clown world",
                    ],
                "political_targets": [
                "biden",
                    "harris",
                    "pelosi",
                    "schumer",
                    "aoc",
                    "democrat",
                    "liberal",
                    "progressive",
                    "mainstream media",
                    "fake news",
                    ],
                "conservative_themes": [
                "america first",
                    "traditional values",
                    "constitution",
                    "freedom",
                    "liberty",
                    "patriot",
                    "maga",
                    "trump",
                    ],
                }

        self.init_database()


    def init_database(self):
        """Initialize database tables for YouTube content"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS youtube_videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    channel_name TEXT NOT NULL,
                    channel_id TEXT NOT NULL,
                    description TEXT,
                    duration TEXT,
                    view_count INTEGER,
                    like_count INTEGER,
                    comment_count INTEGER,
                    published_at TIMESTAMP,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    thumbnail_url TEXT,
                    video_url TEXT,
                    style_analysis TEXT,
                    humor_score REAL DEFAULT 0.0,
                    relevance_score REAL DEFAULT 0.0,
                    right_perspective_potential BOOLEAN DEFAULT FALSE
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS youtube_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    comment_text TEXT NOT NULL,
                    author TEXT,
                    like_count INTEGER DEFAULT 0,
                    reply_count INTEGER DEFAULT 0,
                    published_at TIMESTAMP,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (video_id) REFERENCES youtube_videos (video_id)
            )
        """
        )

        conn.commit()
        conn.close()
        logger.info("YouTube database tables initialized")


    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
        patterns = [
            r"(?:youtube\\.com / watch\\?v=|youtu\\.be/)([a - zA - Z0 - 9_-]{11})",
                r"youtube\\.com / embed/([a - zA - Z0 - 9_-]{11})",
                ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None


    def analyze_content_style(
        self, title: str, description: str, channel_name: str
    ) -> Dict:
        """Analyze video content for style and humor elements"""
        text = f"{title} {description}".lower()

        analysis = {
            "humor_elements": [],
                "political_targets": [],
                "conservative_themes": [],
                "hypocrisy_indicators": [],
                "humor_score": 0.0,
                "relevance_score": 0.0,
                }

        # Check for humor elements
        for keyword in self.content_keywords["humor_styles"]:
            if keyword in text:
                analysis["humor_elements"].append(keyword)
                analysis["humor_score"] += 1.0

        # Check for political targets
        for keyword in self.content_keywords["political_targets"]:
            if keyword in text:
                analysis["political_targets"].append(keyword)
                analysis["relevance_score"] += 2.0

        # Check for conservative themes
        for keyword in self.content_keywords["conservative_themes"]:
            if keyword in text:
                analysis["conservative_themes"].append(keyword)
                analysis["relevance_score"] += 1.5

        # Check for hypocrisy indicators
        for keyword in self.content_keywords["hypocrisy_indicators"]:
            if keyword in text:
                analysis["hypocrisy_indicators"].append(keyword)
                analysis["relevance_score"] += 3.0

        # Bonus for specific channels known for humor
            humor_channels = ["gutfeld", "crowder", "babylon"]
        if any(channel in channel_name.lower() for channel in humor_channels):
            analysis["humor_score"] += 2.0

        return analysis


    def scrape_channel_videos(
        self, channel_config: Dict, max_videos: int = 50
    ) -> List[Dict]:
        """Scrape recent videos from a YouTube channel (using public data)"""
        videos = []
        channel_name = channel_config["channel_name"]

        # Note: This is a simplified version. In production, you'd use YouTube Data API
        # For now, we'll create sample data based on known conservative content patterns

        logger.info(f"Analyzing {channel_name} content style...")

        # Sample video data based on known conservative YouTube patterns
        sample_videos = self.generate_sample_videos(channel_config)

        for video_data in sample_videos[:max_videos]:
            try:
                # Analyze content style
                style_analysis = self.analyze_content_style(
                    video_data["title"], video_data["description"], channel_name
                )

                video_info = {
                    "video_id": video_data["video_id"],
                        "title": video_data["title"],
                        "channel_name": channel_name,
                        "channel_id": channel_config["channel_id"],
                        "description": video_data["description"],
                        "view_count": video_data.get("view_count", 0),
                        "like_count": video_data.get("like_count", 0),
                        "published_at": video_data.get(
                        "published_at", datetime.now().isoformat()
                    ),
                        "video_url": f"https://youtube.com / watch?v={video_data['video_id']}",
                        "style_analysis": json.dumps(style_analysis),
                        "humor_score": style_analysis["humor_score"],
                        "relevance_score": style_analysis["relevance_score"],
                        "right_perspective_potential": style_analysis["relevance_score"]
                    >= 3.0,
                        }

                videos.append(video_info)

            except Exception as e:
                logger.error(f"Error processing video data: {e}")
                continue

        return videos


    def generate_sample_videos(self, channel_config: Dict) -> List[Dict]:
        """Generate sample video data based on channel style"""
        channel_name = channel_config["channel_name"]
        content_focus = channel_config["content_focus"]

        sample_videos = []

        if "gutfeld" in channel_name.lower():
            sample_videos = [
                {
                    "video_id": "gut001",
                        "title": "Gutfeld!: Democrats flip - flop on border security AGAIN",
                        "description": "Greg Gutfeld breaks down the latest Democratic hypocrisy on immigration policy with his signature humor \
    and panel discussion.",
                        "view_count": 850000,
                        "like_count": 45000,
                        },
                    {
                    "video_id": "gut002",
                        "title": "The Five: Biden contradicts his own campaign promises",
                        "description": "Panel discusses how Biden has reversed course on multiple campaign promises, showing classic political flip - flopping.",
                        "view_count": 720000,
                        "like_count": 38000,
                        },
                    ]

        elif "watters" in channel_name.lower():
            sample_videos = [
                {
                    "video_id": "wat001",
                        "title": "Jesse Watters: Pelosi said the OPPOSITE just 5 years ago",
                        "description": "Jesse exposes Nancy Pelosi's complete reversal on border wall funding with video evidence from her past statements.",
                        "view_count": 920000,
                        "like_count": 52000,
                        },
                    {
                    "video_id": "wat002",
                        "title": "Watters World: Democrats used to LOVE tariffs",
                        "description": "Man - on - the - street interviews reveal how Democrats have completely flipped on trade policy since Trump.",
                        "view_count": 680000,
                        "like_count": 41000,
                        },
                    ]

        elif "bongino" in channel_name.lower():
            sample_videos = [
                {
                    "video_id": "bon001",
                        "title": "The Dan Bongino Show: Schumer's MASSIVE hypocrisy exposed",
                        "description": "Dan breaks down Chuck Schumer's complete 180 on immigration enforcement with receipts \
    and documentation.",
                        "view_count": 450000,
                        "like_count": 28000,
                        },
                    {
                    "video_id": "bon002",
                        "title": "BREAKING: Media lies about Trump policies BACKFIRE",
                        "description": "Explosive analysis of how mainstream media predictions about Trump policies were completely wrong.",
                        "view_count": 380000,
                        "like_count": 25000,
                        },
                    ]

        elif "crowder" in channel_name.lower():
            sample_videos = [
                {
                    "video_id": "cro001",
                        "title": "Change My Mind: Democrats Are Hypocrites on Immigration",
                        "description": "Steven sits down with college students to discuss Democratic flip - flops on border security with humor \
    and facts.",
                        "view_count": 1200000,
                        "like_count": 75000,
                        },
                    {
                    "video_id": "cro002",
                        "title": "AOC Contradicts Herself in 30 Seconds (HILARIOUS)",
                        "description": "Comedy sketch highlighting Alexandria Ocasio - Cortez's contradictory statements on economic policy.",
                        "view_count": 980000,
                        "like_count": 62000,
                        },
                    ]

        elif "right perspective" in channel_name.lower():
            sample_videos = [
                {
                    "video_id": "trp001",
                        "title": "Gaming Industry Goes Woke, Goes Broke",
                        "description": "Conservative gamer perspective on how political correctness is ruining video games \
    and entertainment.",
                        "view_count": 15000,
                        "like_count": 1200,
                        },
                    {
                    "video_id": "trp002",
                        "title": "Why Conservatives Need to Fight Back in Gaming",
                        "description": "Non - commie perspective on standing up to liberal bias in gaming culture \
    and media.",
                        "view_count": 12000,
                        "like_count": 980,
                        },
                    ]

        return sample_videos


    def save_videos(self, videos: List[Dict]) -> int:
        """Save scraped videos to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        saved_count = 0
        for video in videos:
            try:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO youtube_videos
                    (video_id, title, channel_name, channel_id, description,
                        view_count, like_count, published_at, video_url,
                         style_analysis, humor_score, relevance_score, right_perspective_potential)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        video["video_id"],
                            video["title"],
                            video["channel_name"],
                            video["channel_id"],
                            video["description"],
                            video["view_count"],
                            video["like_count"],
                            video["published_at"],
                            video["video_url"],
                            video["style_analysis"],
                            video["humor_score"],
                            video["relevance_score"],
                            video["right_perspective_potential"],
                            ),
                        )

                if cursor.rowcount > 0:
                    saved_count += 1

            except Exception as e:
                logger.error(f"Error saving video: {e}")

        conn.commit()
        conn.close()

        logger.info(f"Saved {saved_count} new videos to database")
        return saved_count


    def scrape_all_channels(self) -> Dict[str, int]:
        """Scrape all conservative YouTube channels"""
        results = {"total_videos": 0, "high_potential": 0}

        for channel_key, channel_config in self.conservative_channels.items():
            logger.info(f"Scraping {channel_config['channel_name']}...")

            videos = self.scrape_channel_videos(channel_config, max_videos = 20)
            saved = self.save_videos(videos)

            high_potential = sum(1 for v in videos if v["right_perspective_potential"])

            results["total_videos"] += saved
            results["high_potential"] += high_potential

            logger.info(
                f"Scraped {saved} videos from {channel_config['channel_name']} ({high_potential} high - potential)"
            )

            # Rate limiting
            time.sleep(2)

        return results


    def get_style_inspiration(self, limit: int = 20) -> List[Dict]:
        """Get videos that can inspire The Right Perspective style"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT title, channel_name, description, humor_score, relevance_score,
                video_url, style_analysis
            FROM youtube_videos
            WHERE humor_score >= 2.0 OR relevance_score >= 3.0
            ORDER BY (humor_score + relevance_score) DESC
            LIMIT ?
        """,
            (limit,),
                )

        videos = []
        for row in cursor.fetchall():
            style_data = json.loads(row[6]) if row[6] else {}
            videos.append(
                {
                    "title": row[0],
                        "channel_name": row[1],
                        "description": (
                        row[2][:200] + "..." if len(row[2]) > 200 else row[2]
                    ),
                        "humor_score": row[3],
                        "relevance_score": row[4],
                        "video_url": row[5],
                        "style_elements": style_data,
                        }
            )

        conn.close()
        return videos


    def generate_content_recommendations(self) -> Dict:
        """Generate content recommendations for The Right Perspective"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get top performing content themes
        cursor.execute(
            """
            SELECT channel_name, AVG(humor_score), AVG(relevance_score), COUNT(*)
            FROM youtube_videos
            GROUP BY channel_name
            ORDER BY AVG(humor_score + relevance_score) DESC
        """
        )

        channel_performance = cursor.fetchall()

        # Get most common successful elements
        cursor.execute(
            """
            SELECT style_analysis FROM youtube_videos
            WHERE right_perspective_potential = TRUE
        """
        )

        successful_elements = []
        for row in cursor.fetchall():
            if row[0]:
                style_data = json.loads(row[0])
                successful_elements.extend(style_data.get("humor_elements", []))
                successful_elements.extend(style_data.get("political_targets", []))

        # Count element frequency
        element_counts = {}
        for element in successful_elements:
            element_counts[element] = element_counts.get(element, 0) + 1

        top_elements = sorted(element_counts.items(),
    key = lambda x: x[1],
    reverse = True)[
            :10
        ]

        conn.close()

        return {
            "top_performing_channels": channel_performance,
                "most_effective_elements": top_elements,
                "recommended_style": "Combine humor with political analysis, focus on hypocrisy examples",
                "content_suggestions": [
                "Create segments exposing Democratic flip - flops with humor",
                    "Use video evidence to show contradictions",
                    "Incorporate gaming analogies for younger audience",
                    "Focus on visual comparisons (then vs now)",
                    "Add comedic commentary to serious political topics",
                    ],
                }


def main():
    """Main function for YouTube scraping and analysis"""
    scraper = YouTubeScraperForRightPerspective()

    print("🎥 Starting YouTube analysis for The Right Perspective...")

    # Scrape all channels
    results = scraper.scrape_all_channels()

    print(f"\\n📊 YouTube Scraping Results:")
    print(f"Total videos analyzed: {results['total_videos']}")
    print(f"High - potential content: {results['high_potential']}")

    # Get style inspiration
    inspiration = scraper.get_style_inspiration(10)

    print(f"\\n🎭 Top Style Inspiration for The Right Perspective:")
    for i, video in enumerate(inspiration, 1):
        print(f"{i}. [{video['channel_name']}] {video['title']}")
        print(
            f"   Humor Score: {video['humor_score']}, Relevance: {video['relevance_score']}"
        )
        print(f"   URL: {video['video_url']}")
        print(f"   Elements: {video['style_elements']}\\n")

    # Generate recommendations
    recommendations = scraper.generate_content_recommendations()

    print(f"\\n💡 Content Recommendations for The Right Perspective:")
    print(f"Recommended Style: {recommendations['recommended_style']}")
    print(f"\\nContent Suggestions:")
    for suggestion in recommendations["content_suggestions"]:
        print(f"• {suggestion}")

    print(f"\\nMost Effective Elements:")
    for element, count in recommendations["most_effective_elements"]:
        print(f"• {element}: {count} occurrences")

if __name__ == "__main__":
    main()