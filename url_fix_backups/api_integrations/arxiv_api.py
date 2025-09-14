import asyncio
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from .base_api import APIError, BaseAPI, RateLimitConfig

logger = logging.getLogger(__name__)


class ArxivAPI(BaseAPI):
    """arXiv API integration for academic research analysis"""

    def __init__(self):
        # arXiv API is free but has rate limits
        rate_config = RateLimitConfig(
            requests_per_minute=20,  # Conservative rate limiting
            requests_per_hour=300,
            requests_per_day=3000,
            burst_limit=5,
        )
        super().__init__(rate_config)
        self.base_url = "http://export.arxiv.org / api / query"

        # arXiv subject categories
        self.categories = {
            "cs": "Computer Science",
            "math": "Mathematics",
            "physics": "Physics",
            "q - bio": "Quantitative Biology",
            "q - fin": "Quantitative Finance",
            "stat": "Statistics",
            "eess": "Electrical Engineering and Systems Science",
            "econ": "Economics",
        }

    async def health_check(self) -> bool:
        """Check if arXiv API is accessible"""
        try:
            # Simple test query
            result = await self.search_papers(query="machine learning", max_results=1)
            return len(result.get("papers", [])) > 0
        except Exception as e:
            logger.error(f"arXiv health check failed: {e}")
            return False

    async def get_quota_status(self) -> Dict[str, Any]:
        """Get current quota status"""
        return {
            "service": "arXiv API",
            "daily_limit": self.rate_limiter.config.requests_per_day,
            "daily_used": self.rate_limiter.daily_count,
            "hourly_limit": self.rate_limiter.config.requests_per_hour,
            "hourly_used": self.rate_limiter.hourly_count,
            "tokens_available": int(self.rate_limiter.tokens),
            "cost": "Free",
        }

    async def search_papers(
        self,
        query: str,
        category: Optional[str] = None,
        max_results: int = 50,
        sort_by: str = "submittedDate",
        sort_order: str = "descending",
        start: int = 0,
    ) -> Dict[str, Any]:
        """Search arXiv papers"""
        await self.rate_limiter.acquire()

        # Build search query
        search_query = query
        if category:
            search_query = f"cat:{category} AND ({query})"

        params = {
            "search_query": search_query,
            "start": start,
            "max_results": min(max_results, 2000),  # arXiv limit
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }

        try:
            # Make request to arXiv API
            response_text = await self._make_arxiv_request(params)

            # Parse XML response
            papers = self._parse_arxiv_response(response_text)

            return {
                "query": query,
                "category": category,
                "total_results": len(papers),
                "papers": papers,
                "search_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            raise APIError(f"Failed to search arXiv papers: {e}")

    async def get_recent_papers(
        self, category: str, days_back: int = 7, max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent papers from a specific category"""
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)

        # Format dates for arXiv query
        date_query = f'submittedDate:[{start_date.strftime("%Y % m%d")}* TO {end_date.strftime("%Y % m%d")}*]'

        try:
            result = await self.search_papers(
                query=date_query,
                category=category,
                max_results=max_results,
                sort_by="submittedDate",
                sort_order="descending",
            )

            return result.get("papers", [])

        except Exception as e:
            raise APIError(f"Failed to get recent papers: {e}")

    async def analyze_research_trends(
        self,
        keywords: List[str],
        categories: List[str] = None,
        time_period_days: int = 30,
    ) -> Dict[str, Any]:
        """Analyze research trends for given keywords"""
        if not categories:
            categories = ["cs", "math", "physics", "stat"]

        try:
            trend_data = {}

            for keyword in keywords:
                keyword_data = {
                    "keyword": keyword,
                    "categories": {},
                    "total_papers": 0,
                    "recent_papers": 0,
                }

                for category in categories:
                    try:
                        # Get all papers for this keyword / category
                        all_papers = await self.search_papers(
                            query=keyword, category=category, max_results=500
                        )

                        # Get recent papers
                        recent_papers = await self.get_recent_papers(
                            category=category,
                            days_back=time_period_days,
                            max_results=100,
                        )

                        # Filter recent papers by keyword
                        relevant_recent = [
                            paper
                            for paper in recent_papers
                            if keyword.lower() in paper.get("title", "").lower()
                            or keyword.lower() in paper.get("summary", "").lower()
                        ]

                        category_stats = {
                            "total_papers": len(all_papers.get("papers", [])),
                            "recent_papers": len(relevant_recent),
                            "growth_rate": 0,
                            "top_papers": relevant_recent[:5],  # Top 5 recent papers
                        }

                        # Calculate growth rate
                        if category_stats["total_papers"] > 0:
                            category_stats["growth_rate"] = (
                                category_stats["recent_papers"]
                                / max(category_stats["total_papers"], 1)
                            ) * 100

                        keyword_data["categories"][category] = category_stats
                        keyword_data["total_papers"] += category_stats["total_papers"]
                        keyword_data["recent_papers"] += category_stats["recent_papers"]

                        # Add delay between requests
                        await asyncio.sleep(1)

                    except Exception as e:
                        logger.warning(f"Failed to analyze {keyword} in {category}: {e}")
                        continue

                # Calculate overall trend score
                if keyword_data["total_papers"] > 0:
                    keyword_data["trend_score"] = (
                        keyword_data["recent_papers"] / max(keyword_data["total_papers"], 1)
                    ) * 100
                else:
                    keyword_data["trend_score"] = 0

                trend_data[keyword] = keyword_data

            # Rank keywords by trend score
            ranked_keywords = sorted(
                trend_data.items(), key=lambda x: x[1]["trend_score"], reverse=True
            )

            return {
                "keywords": trend_data,
                "ranked_keywords": [{"keyword": k, **v} for k, v in ranked_keywords],
                "analysis_period_days": time_period_days,
                "categories_analyzed": categories,
                "analysis_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            raise APIError(f"Failed to analyze research trends: {e}")

    async def get_paper_details(self, arxiv_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific paper"""
        await self.rate_limiter.acquire()

        try:
            result = await self.search_papers(query=f"id:{arxiv_id}", max_results=1)

            papers = result.get("papers", [])
            if not papers:
                raise APIError(f"Paper {arxiv_id} not found")

            return papers[0]

        except Exception as e:
            raise APIError(f"Failed to get paper details: {e}")

    async def find_emerging_topics(
        self, categories: List[str] = None, days_back: int = 30, min_papers: int = 5
    ) -> Dict[str, Any]:
        """Find emerging research topics"""
        if not categories:
            categories = ["cs", "math", "physics", "stat"]

        try:
            topic_analysis = {}
            all_papers = []

            # Collect recent papers from all categories
            for category in categories:
                try:
                    recent_papers = await self.get_recent_papers(
                        category=category, days_back=days_back, max_results=200
                    )

                    for paper in recent_papers:
                        paper["category"] = category
                        all_papers.append(paper)

                    await asyncio.sleep(1)  # Rate limiting

                except Exception as e:
                    logger.warning(f"Failed to get papers from {category}: {e}")
                    continue

            if not all_papers:
                return {
                    "emerging_topics": [],
                    "total_papers_analyzed": 0,
                    "error": "No papers found",
                }

            # Extract keywords from titles and abstracts
            keyword_counts = {}
            keyword_papers = {}

            for paper in all_papers:
                # Simple keyword extraction (can be enhanced with NLP)
                text = f"{paper.get('title', '')} {paper.get('summary', '')}".lower()
                words = text.split()

                # Filter for meaningful keywords
                for word in words:
                    if (
                        len(word) > 4
                        and word.isalpha()
                        and word
                        not in [
                            "paper",
                            "study",
                            "research",
                            "analysis",
                            "method",
                            "approach",
                        ]
                    ):
                        if word not in keyword_counts:
                            keyword_counts[word] = 0
                            keyword_papers[word] = []

                        keyword_counts[word] += 1
                        if len(keyword_papers[word]) < 5:  # Keep top 5 papers per keyword
                            keyword_papers[word].append(
                                {
                                    "title": paper.get("title", ""),
                                    "authors": paper.get("authors", []),
                                    "category": paper.get("category", ""),
                                    "published": paper.get("published", ""),
                                }
                            )

            # Filter and rank emerging topics
            emerging_topics = []
            for keyword, count in keyword_counts.items():
                if count >= min_papers:
                    # Calculate emergence score based on frequency and recency
                    emergence_score = count * (days_back / 30)  # Normalize by time period

                    emerging_topics.append(
                        {
                            "topic": keyword,
                            "paper_count": count,
                            "emergence_score": round(emergence_score, 2),
                            "sample_papers": keyword_papers[keyword],
                            "categories": list(
                                set(paper["category"] for paper in keyword_papers[keyword])
                            ),
                        }
                    )

            # Sort by emergence score
            emerging_topics.sort(key=lambda x: x["emergence_score"], reverse=True)

            return {
                "emerging_topics": emerging_topics[:20],  # Top 20 topics
                "total_papers_analyzed": len(all_papers),
                "analysis_period_days": days_back,
                "categories_analyzed": categories,
                "analysis_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            raise APIError(f"Failed to find emerging topics: {e}")

    async def _make_arxiv_request(self, params: Dict[str, Any]) -> str:
        """Make request to arXiv API and return raw text"""
        if not self.session:
            raise APIError("Session not initialized")

        try:
            async with self.session.get(self.base_url, params=params) as response:
                if response.status != 200:
                    raise APIError(f"arXiv API returned status {response.status}")

                return await response.text()

        except Exception as e:
            raise APIError(f"Failed to make arXiv request: {e}")

    def _parse_arxiv_response(self, xml_text: str) -> List[Dict[str, Any]]:
        """Parse arXiv XML response into structured data"""
        try:
            root = ET.fromstring(xml_text)

            # Define namespaces
            namespaces = {
                "atom": "http://www.w3.org / 2005 / Atom",
                "arxiv": "http://arxiv.org / schemas / atom",
            }

            papers = []

            for entry in root.findall("atom:entry", namespaces):
                paper = {}

                # Basic information
                paper["id"] = (
                    entry.find("atom:id", namespaces).text
                    if entry.find("atom:id", namespaces) is not None
                    else ""
                )
                paper["title"] = (
                    entry.find("atom:title", namespaces).text.strip()
                    if entry.find("atom:title", namespaces) is not None
                    else ""
                )
                paper["summary"] = (
                    entry.find("atom:summary", namespaces).text.strip()
                    if entry.find("atom:summary", namespaces) is not None
                    else ""
                )

                # Published and updated dates
                published = entry.find("atom:published", namespaces)
                paper["published"] = published.text if published is not None else ""

                updated = entry.find("atom:updated", namespaces)
                paper["updated"] = updated.text if updated is not None else ""

                # Authors
                authors = []
                for author in entry.findall("atom:author", namespaces):
                    name = author.find("atom:name", namespaces)
                    if name is not None:
                        authors.append(name.text)
                paper["authors"] = authors

                # Categories
                categories = []
                for category in entry.findall("atom:category", namespaces):
                    term = category.get("term")
                    if term:
                        categories.append(term)
                paper["categories"] = categories

                # Primary category
                primary_cat = entry.find("arxiv:primary_category", namespaces)
                paper["primary_category"] = (
                    primary_cat.get("term") if primary_cat is not None else ""
                )

                # Links
                links = {}
                for link in entry.findall("atom:link", namespaces):
                    rel = link.get("rel", "")
                    href = link.get("href", "")
                    if rel and href:
                        links[rel] = href
                paper["links"] = links

                # DOI if available
                doi = entry.find("arxiv:doi", namespaces)
                paper["doi"] = doi.text if doi is not None else ""

                # Comment if available
                comment = entry.find("arxiv:comment", namespaces)
                paper["comment"] = comment.text if comment is not None else ""

                papers.append(paper)

            return papers

        except ET.ParseError as e:
            raise APIError(f"Failed to parse arXiv XML response: {e}")
        except Exception as e:
            raise APIError(f"Error processing arXiv response: {e}")
