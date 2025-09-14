#!/usr/bin/env python3
"""
News Scraper for The Right Perspective
Scrapes conservative and mainstream news sources for content analysis
"""

import json
import logging
import random
import re
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level = logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NewsScraperForRightPerspective:


    def __init__(self, db_path: str = "conservative_research.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User - Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML,"
"""[PRESERVED-BROKEN-LINE] closing parenthesis ')' does not match opening parenthesis '{' on line 34 (news_scraper.py, line 36)"""
#     like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

        # News sources configuration for The Right Perspective research
        self.news_sources = {
            "conservative": {
                "fox_news": {
                    "base_url": "https://www.foxnews.com",
                        "sections": ["/politics", "/opinion", "/media"],
                        "article_selector": "article h2 a, .title a",
                        "content_selector": ".article - body p, .speakable p",
                        },
                    "drudge_report": {
                    "base_url": "https://www.drudgereport.com",
                        "sections": [""],
                        "article_selector": 'a[href*="http"]',
                        "content_selector": "p",
                        },
                    "babylon_bee": {
                    "base_url": "https://babylonbee.com",
                        "sections": ["/politics", "/news"],
                        "article_selector": ".bb - article - title a",
                        "content_selector": ".bb - article - content p",
                        },
                    "daily_wire": {
                    "base_url": "https://www.dailywire.com",
                        "sections": ["/news/politics", "/news"],
                        "article_selector": ".field - title a",
                        "content_selector": ".field - body p",
                        },
                    "breitbart": {
                    "base_url": "https://www.breitbart.com",
                        "sections": ["/politics", "/big - government"],
                        "article_selector": "h2 a, .title a",
                        "content_selector": ".entry - content p",
                        },
                    },
                "mainstream": {
                "cnn": {
                    "base_url": "https://www.cnn.com",
                        "sections": ["/politics"],
                        "article_selector": ".container__headline a",
                        "content_selector": ".zn - body__paragraph",
                        },
                    "msnbc": {
                    "base_url": "https://www.msnbc.com",
                        "sections": ["/politics"],
                        "article_selector": ".tease - card__headline a",
                        "content_selector": ".articleBody p",
                        },
                    "washington_post": {
                    "base_url": "https://www.washingtonpost.com",
                        "sections": ["/politics"],
                        "article_selector": ".headline a",
                        "content_selector": ".article - body p",
                        },
                    },
                }

        # Keywords for The Right Perspective content identification
        self.target_keywords = [
            # Democratic hypocrisy keywords
            "biden",
                "harris",
                "pelosi",
                "schumer",
                "aoc",
                "ocasio - cortez",
                "democrat",
                "democratic",
                "liberal",
                "progressive",
                # Policy flip - flop keywords
            "border wall",
                "immigration",
                "tariffs",
                "trade war",
                "russia collusion",
                "steele dossier",
                "fake news",
                # Conservative talking points
            "hypocrisy",
                "flip - flop",
                "contradiction",
                "lies",
                "double standard",
                "mainstream media bias",
                ]

        self.init_database()


    def init_database(self):
        """Initialize database tables for scraped news articles"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scraped_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    source TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    content TEXT,
                    summary TEXT,
                    keywords TEXT,
                    relevance_score REAL DEFAULT 0.0,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    published_at TIMESTAMP,
                    right_perspective_potential BOOLEAN DEFAULT FALSE
            )
        """
        )

        conn.commit()
        conn.close()
        logger.info("Database initialized for news scraping")


    def calculate_relevance_score(self, title: str, content: str) -> float:
        """Calculate relevance score for The Right Perspective content"""
        text = f"{title} {content}".lower()
        score = 0.0

        # Higher scores for conservative talking points
        high_value_keywords = [
            "hypocrisy",
                "flip - flop",
                "double standard",
                "lies",
                "fake news",
                ]
        for keyword in high_value_keywords:
            if keyword in text:
                score += 3.0

        # Medium scores for political figures
        political_keywords = ["biden", "harris", "pelosi", "schumer", "democrat"]
        for keyword in political_keywords:
            if keyword in text:
                score += 2.0

        # Base scores for general keywords
        for keyword in self.target_keywords:
            if keyword in text:
                score += 1.0

        return min(score, 10.0)  # Cap at 10.0


    def scrape_article_content(self, url: str, content_selector: str) -> Optional[str]:
        """Scrape full article content from URL"""
        try:
            response = self.session.get(url, timeout = 10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Try multiple selectors
            selectors = [
                content_selector,
                    "p",
                    ".content p",
                    ".article p",
                    ".post - content p",
                    ]

            for selector in selectors:
                paragraphs = soup.select(selector)
                if paragraphs:
                    content = " ".join(
                        [p.get_text().strip() for p in paragraphs[:10]]
                    )  # First 10 paragraphs
                    if len(content) > 100:  # Minimum content length
                        return content

            return None

        except Exception as e:
            logger.warning(f"Failed to scrape content from {url}: {e}")
            return None


    def scrape_source(
        self, source_name: str, source_config: Dict, source_type: str
    ) -> List[Dict]:
        """Scrape articles from a specific news source"""
        articles = []
        base_url = source_config["base_url"]

        for section in source_config["sections"]:
            try:
                url = f"{base_url}{section}"
                logger.info(f"Scraping {source_name} section: {url}")

                response = self.session.get(url, timeout = 10)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, "html.parser")
                article_links = soup.select(source_config["article_selector"])

                for link in article_links[:20]:  # Limit to 20 articles per section
                    try:
                        article_url = link.get("href")
                        if not article_url:
                            continue

                        # Handle relative URLs
                        if article_url.startswith("/"):
                            article_url = urljoin(base_url, article_url)
                        elif not article_url.startswith("http"):
                            continue

                        title = link.get_text().strip()
                        if not title or len(title) < 10:
                            continue

                        # Check if article is relevant to The Right Perspective
                        relevance_score = self.calculate_relevance_score(title, "")

                        if relevance_score >= 1.0:  # Only scrape relevant articles
                            # Scrape full content
                            content = self.scrape_article_content(
                                article_url, source_config["content_selector"]
                            )

                            if content:
                                # Recalculate score with full content
                                relevance_score = self.calculate_relevance_score(
                                    title, content
                                )

                                articles.append(
                                    {
                                        "title": title,
                                            "url": article_url,
                                            "source": source_name,
                                            "source_type": source_type,
                                            "content": content,
                                            "relevance_score": relevance_score,
                                            "right_perspective_potential": relevance_score
                                        >= 3.0,
                                            }
                                )

                        # Rate limiting
                        time.sleep(random.uniform(1, 3))

                    except Exception as e:
                        logger.warning(f"Error processing article link: {e}")
                        continue

            except Exception as e:
                logger.error(f"Error scraping {source_name} section {section}: {e}")
                continue

        return articles


    def save_articles(self, articles: List[Dict]):
        """Save scraped articles to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        saved_count = 0
        for article in articles:
            try:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO scraped_articles
                    (title,
    url,
    source,
    source_type,
    content,
    relevance_score,
    right_perspective_potential)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        article["title"],
                            article["url"],
                            article["source"],
                            article["source_type"],
                            article["content"],
                            article["relevance_score"],
                            article["right_perspective_potential"],
                            ),
                        )

                if cursor.rowcount > 0:
                    saved_count += 1

            except Exception as e:
                logger.error(f"Error saving article: {e}")

        conn.commit()
        conn.close()

        logger.info(f"Saved {saved_count} new articles to database")
        return saved_count


    def scrape_all_sources(self) -> Dict[str, int]:
        """Scrape all configured news sources for The Right Perspective"""
        results = {"conservative": 0, "mainstream": 0, "total": 0}

        # Scrape conservative sources
        logger.info("Scraping conservative news sources...")
        for source_name, config in self.news_sources["conservative"].items():
            articles = self.scrape_source(source_name, config, "conservative")
            saved = self.save_articles(articles)
            results["conservative"] += saved
            logger.info(f"Scraped {saved} articles from {source_name}")

            # Rate limiting between sources
            time.sleep(random.uniform(5, 10))

        # Scrape mainstream sources for comparison
        logger.info("Scraping mainstream news sources...")
        for source_name, config in self.news_sources["mainstream"].items():
            articles = self.scrape_source(source_name, config, "mainstream")
            saved = self.save_articles(articles)
            results["mainstream"] += saved
            logger.info(f"Scraped {saved} articles from {source_name}")

            # Rate limiting between sources
            time.sleep(random.uniform(5, 10))

        results["total"] = results["conservative"] + results["mainstream"]
        return results


    def get_high_potential_articles(self, limit: int = 50) -> List[Dict]:
        """Get articles with high potential for The Right Perspective content"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT title, url, source, source_type, content, relevance_score, scraped_at
            FROM scraped_articles
            WHERE right_perspective_potential = TRUE
            ORDER BY relevance_score DESC, scraped_at DESC
            LIMIT ?
        """,
            (limit,),
                )

        articles = []
        for row in cursor.fetchall():
            articles.append(
                {
                    "title": row[0],
                        "url": row[1],
                        "source": row[2],
                        "source_type": row[3],
                        "content": row[4][:500] + "..." if len(row[4]) > 500 else row[4],
                        "relevance_score": row[5],
                        "scraped_at": row[6],
                        }
            )

        conn.close()
        return articles


    def generate_content_summary(self) -> Dict:
        """Generate summary of scraped content for The Right Perspective"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get statistics
        cursor.execute("SELECT COUNT(*) FROM scraped_articles")
        total_articles = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM scraped_articles WHERE right_perspective_potential = TRUE"
        )
        high_potential = cursor.fetchone()[0]

        cursor.execute(
            "SELECT source_type, COUNT(*) FROM scraped_articles GROUP BY source_type"
        )
        by_source_type = dict(cursor.fetchall())

        cursor.execute(
            """
            SELECT source, COUNT(*) FROM scraped_articles
            WHERE right_perspective_potential = TRUE
            GROUP BY source ORDER BY COUNT(*) DESC
        """
        )
        top_sources = cursor.fetchall()

        conn.close()

        return {
            "total_articles": total_articles,
                "high_potential_articles": high_potential,
                "by_source_type": by_source_type,
                "top_sources_for_content": top_sources[:5],
                "potential_percentage": (
                round((high_potential/total_articles * 100), 2)
                if total_articles > 0
                else 0
            ),
                }


def main():
    """Main function for The Right Perspective news scraping"""
    scraper = NewsScraperForRightPerspective()

    print("🔍 Starting news scraping for The Right Perspective...")

    # Scrape all sources
    results = scraper.scrape_all_sources()

    print(f"\\n📊 Scraping Results:")
    print(f"Conservative sources: {results['conservative']} articles")
    print(f"Mainstream sources: {results['mainstream']} articles")
    print(f"Total articles: {results['total']} articles")

    # Get high potential articles
    high_potential = scraper.get_high_potential_articles(10)

    print(f"\\n🎯 Top High - Potential Articles for The Right Perspective:")
    for i, article in enumerate(high_potential, 1):
        print(
            f"{i}. [{article['source']}] {article['title']} (Score: {article['relevance_score']})"
        )
        print(f"   URL: {article['url']}")
        print(f"   Preview: {article['content'][:100]}...\\n")

    # Generate summary
    summary = scraper.generate_content_summary()
    print(f"\\n📈 Content Summary:")
    print(f"Total articles scraped: {summary['total_articles']}")
    print(
        f"High - potential articles: {summary['high_potential_articles']} ({summary['potential_percentage']}%)"
    )
    print(f"By source type: {summary['by_source_type']}")
    print(f"Top sources for content: {summary['top_sources_for_content']}")

if __name__ == "__main__":
    main()
