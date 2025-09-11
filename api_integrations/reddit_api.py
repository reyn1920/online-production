import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import praw
from textblob import TextBlob

from .base_api import APIError, BaseAPI, RateLimitConfig

logger = logging.getLogger(__name__)


class RedditAPI(BaseAPI):
    """Reddit API integration using PRAW"""


    def __init__(
        self, client_id: str = None, client_secret: str = None, user_agent: str = None
    ):
        # Reddit API rate limits: 60 requests per minute
        rate_config = RateLimitConfig(
            requests_per_minute = 50,  # Conservative limit
            requests_per_hour = 1000,
                requests_per_day = 10000,
                burst_limit = 5,
                )
        super().__init__(rate_config)

        # Use read - only mode if no credentials provided (zero - cost approach)
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent or "NicheDiscoveryEngine:v1.0 (by /u / researcher)"
        self.reddit = None


    async def _init_reddit(self):
        """Initialize Reddit client"""
        if not self.reddit:
            try:
                loop = asyncio.get_event_loop()

                if self.client_id and self.client_secret:
                    # Authenticated mode
                    self.reddit = await loop.run_in_executor(
                        None,
                            lambda: praw.Reddit(
                            client_id = self.client_id,
                                client_secret = self.client_secret,
                                user_agent = self.user_agent,
                                ),
                            )
                else:
                    # Read - only mode (zero - cost)
                    self.reddit = await loop.run_in_executor(
                        None,
                            lambda: praw.Reddit(
                            client_id="dummy",
                                client_secret="dummy",
                                user_agent = self.user_agent,
                                check_for_async = False,
                                ),
                            )

            except Exception as e:
                raise APIError(f"Failed to initialize Reddit client: {e}")


    async def health_check(self) -> bool:
        """Check if Reddit API is accessible"""
        try:
            await self._init_reddit()
            # Test with a simple subreddit access
            loop = asyncio.get_event_loop()
            subreddit = await loop.run_in_executor(
                None, lambda: self.reddit.subreddit("python")
            )
            # Try to get one post
            await loop.run_in_executor(None, lambda: next(subreddit.hot(limit = 1)))
            return True
        except Exception as e:
            logger.error(f"Reddit health check failed: {e}")
            return False


    async def get_quota_status(self) -> Dict[str, Any]:
        """Get current quota status"""
        return {
            "service": "Reddit API (PRAW)",
                "daily_limit": self.rate_limiter.config.requests_per_day,
                "daily_used": self.rate_limiter.daily_count,
                "hourly_limit": self.rate_limiter.config.requests_per_hour,
                "hourly_used": self.rate_limiter.hourly_count,
                "tokens_available": int(self.rate_limiter.tokens),
                "authenticated": bool(self.client_id and self.client_secret),
                }


    async def search_subreddits(
        self, query: str, limit: int = 25
    ) -> List[Dict[str, Any]]:
        """Search for subreddits related to query"""
        await self.rate_limiter.acquire()
        await self._init_reddit()

        try:
            loop = asyncio.get_event_loop()
            subreddits = await loop.run_in_executor(
                None, lambda: list(self.reddit.subreddits.search(query, limit = limit))
            )

            results = []
            for subreddit in subreddits:
                results.append(
                    {
                        "name": subreddit.display_name,
                            "title": subreddit.title,
                            "description": subreddit.public_description,
                            "subscribers": subreddit.subscribers,
                            "created_utc": datetime.fromtimestamp(
                            subreddit.created_utc
                        ).isoformat(),
                            "over18": subreddit.over18,
                            "url": f"https://reddit.com / r/{subreddit.display_name}",
                            }
                )

            return results

        except Exception as e:
            raise APIError(f"Failed to search subreddits: {e}")


    async def get_subreddit_posts(
        self,
            subreddit_name: str,
            sort: str = "hot",
            time_filter: str = "week",
            limit: int = 25,
            ) -> List[Dict[str, Any]]:
        """Get posts from a subreddit"""
        await self.rate_limiter.acquire()
        await self._init_reddit()

        try:
            loop = asyncio.get_event_loop()
            subreddit = await loop.run_in_executor(
                None, lambda: self.reddit.subreddit(subreddit_name)
            )

            # Get posts based on sort type
            if sort == "hot":
                posts = await loop.run_in_executor(
                    None, lambda: list(subreddit.hot(limit = limit))
                )
            elif sort == "top":
                posts = await loop.run_in_executor(
                    None,
                        lambda: list(subreddit.top(time_filter = time_filter, limit = limit)),
                        )
            elif sort == "new":
                posts = await loop.run_in_executor(
                    None, lambda: list(subreddit.new(limit = limit))
                )
            else:
                raise APIError(f"Invalid sort type: {sort}")

            results = []
            for post in posts:
                # Calculate engagement metrics
                engagement_rate = (post.num_comments / max(post.score, 1)) * 100

                results.append(
                    {
                        "id": post.id,
                            "title": post.title,
                            "selftext": (
                            post.selftext[:500] if post.selftext else ""
                        ),  # Truncate long text
                        "score": post.score,
                            "upvote_ratio": post.upvote_ratio,
                            "num_comments": post.num_comments,
                            "created_utc": datetime.fromtimestamp(
                            post.created_utc
                        ).isoformat(),
                            "author": str(post.author) if post.author else "[deleted]",
                            "url": post.url,
                            "permalink": f"https://reddit.com{post.permalink}",
                            "subreddit": post.subreddit.display_name,
                            "over_18": post.over_18,
                            "is_self": post.is_self,
                            "engagement_rate": round(engagement_rate, 2),
                            "flair_text": post.link_flair_text,
                            }
                )

            return results

        except Exception as e:
            raise APIError(f"Failed to get subreddit posts: {e}")


    async def get_post_comments(
        self, post_id: str, limit: int = 50, sort: str = "top"
    ) -> List[Dict[str, Any]]:
        """Get comments from a specific post"""
        await self.rate_limiter.acquire()
        await self._init_reddit()

        try:
            loop = asyncio.get_event_loop()
            submission = await loop.run_in_executor(
                None, lambda: self.reddit.submission(id = post_id)
            )

            # Set comment sort and limit
            submission.comment_sort = sort
            submission.comment_limit = limit

            # Get comments
            await loop.run_in_executor(
                None, lambda: submission.comments.replace_more(limit = 0)
            )

            comments = await loop.run_in_executor(
                None, lambda: list(submission.comments.list())
            )

            results = []
            for comment in comments[:limit]:
                if hasattr(comment, "body") and comment.body != "[deleted]":
                    # Perform sentiment analysis
                    sentiment = self._analyze_sentiment(comment.body)

                    results.append(
                        {
                            "id": comment.id,
                                "body": comment.body[:1000],  # Truncate long comments
                            "score": comment.score,
                                "created_utc": datetime.fromtimestamp(
                                comment.created_utc
                            ).isoformat(),
                                "author": (
                                str(comment.author) if comment.author else "[deleted]"
                            ),
                                "permalink": f"https://reddit.com{comment.permalink}",
                                "is_submitter": comment.is_submitter,
                                "sentiment": sentiment,
                                "depth": comment.depth if hasattr(comment, "depth") else 0,
                                }
                    )

            return results

        except Exception as e:
            raise APIError(f"Failed to get post comments: {e}")


    async def analyze_subreddit_sentiment(
        self, subreddit_name: str, limit: int = 100
    ) -> Dict[str, Any]:
        """Analyze overall sentiment of a subreddit"""
        try:
            # Get recent posts
            posts = await self.get_subreddit_posts(
                subreddit_name, sort="hot", limit = limit
            )

            if not posts:
                return {
                    "subreddit": subreddit_name,
                        "sentiment_score": 0,
                        "sentiment_label": "neutral",
                        "post_count": 0,
                        "error": "No posts found",
                        }

            # Analyze sentiment of titles and text
            sentiments = []
            for post in posts:
                text = f"{post['title']} {post['selftext']}"
                sentiment = self._analyze_sentiment(text)
                sentiments.append(sentiment)

            # Calculate overall metrics
            avg_polarity = sum(s["polarity"] for s in sentiments) / len(sentiments)
            avg_subjectivity = sum(s["subjectivity"] for s in sentiments) / len(
                sentiments
            )

            # Determine overall sentiment label
            if avg_polarity > 0.1:
                sentiment_label = "positive"
            elif avg_polarity < -0.1:
                sentiment_label = "negative"
            else:
                sentiment_label = "neutral"

            return {
                "subreddit": subreddit_name,
                    "sentiment_score": round(avg_polarity, 3),
                    "sentiment_label": sentiment_label,
                    "subjectivity": round(avg_subjectivity, 3),
                    "post_count": len(posts),
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                    "sentiment_distribution": {
                    "positive": len([s for s in sentiments if s["polarity"] > 0.1]),
                        "neutral": len(
                        [s for s in sentiments if -0.1 <= s["polarity"] <= 0.1]
                    ),
                        "negative": len([s for s in sentiments if s["polarity"] < -0.1]),
                        },
                    }

        except Exception as e:
            raise APIError(f"Failed to analyze subreddit sentiment: {e}")


    async def find_trending_topics(
        self,
            subreddit_names: List[str],
            time_filter: str = "day",
            limit_per_subreddit: int = 25,
            ) -> Dict[str, Any]:
        """Find trending topics across multiple subreddits"""
        try:
            all_posts = []

            # Collect posts from all subreddits
            for subreddit_name in subreddit_names:
                try:
                    posts = await self.get_subreddit_posts(
                        subreddit_name,
                            sort="top",
                            time_filter = time_filter,
                            limit = limit_per_subreddit,
                            )
                    all_posts.extend(posts)
                except Exception as e:
                    logger.warning(f"Failed to get posts from r/{subreddit_name}: {e}")
                    continue

            if not all_posts:
                return {
                    "trending_topics": [],
                        "subreddits_analyzed": subreddit_names,
                        "total_posts": 0,
                        "error": "No posts found",
                        }

            # Extract and rank topics by engagement
            topic_metrics = {}

            for post in all_posts:
                title_words = post["title"].lower().split()

                # Simple keyword extraction (can be enhanced with NLP)
                for word in title_words:
                    if (
                        len(word) > 3 and word.isalpha()
                    ):  # Filter short words and non - alphabetic
                        if word not in topic_metrics:
                            topic_metrics[word] = {
                                "mentions": 0,
                                    "total_score": 0,
                                    "total_comments": 0,
                                    "posts": [],
                                    }

                        topic_metrics[word]["mentions"] += 1
                        topic_metrics[word]["total_score"] += post["score"]
                        topic_metrics[word]["total_comments"] += post["num_comments"]
                        topic_metrics[word]["posts"].append(
                            {
                                "title": post["title"],
                                    "score": post["score"],
                                    "subreddit": post["subreddit"],
                                    }
                        )

            # Rank topics by combined metrics
            ranked_topics = []
            for topic, metrics in topic_metrics.items():
                if metrics["mentions"] >= 2:  # Only topics mentioned multiple times
                    avg_score = metrics["total_score"] / metrics["mentions"]
                    avg_comments = metrics["total_comments"] / metrics["mentions"]

                    # Calculate trending score
                    trending_score = (
                        metrics["mentions"] * 0.3 + avg_score * 0.4 + avg_comments * 0.3
                    )

                    ranked_topics.append(
                        {
                            "topic": topic,
                                "mentions": metrics["mentions"],
                                "avg_score": round(avg_score, 2),
                                "avg_comments": round(avg_comments, 2),
                                "trending_score": round(trending_score, 2),
                                "sample_posts": metrics["posts"][:3],  # Top 3 posts
                        }
                    )

            # Sort by trending score
            ranked_topics.sort(key = lambda x: x["trending_score"], reverse = True)

            return {
                "trending_topics": ranked_topics[:20],  # Top 20 topics
                "subreddits_analyzed": subreddit_names,
                    "total_posts": len(all_posts),
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                    }

        except Exception as e:
            raise APIError(f"Failed to find trending topics: {e}")


    def _analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of text using TextBlob"""
        try:
            blob = TextBlob(text)
            return {
                "polarity": blob.sentiment.polarity,  # -1 to 1
                "subjectivity": blob.sentiment.subjectivity,  # 0 to 1
            }
        except Exception:
            return {"polarity": 0.0, "subjectivity": 0.0}
