import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .base_api import APIError, BaseAPI, RateLimitConfig

logger = logging.getLogger(__name__)


class GitHubAPI(BaseAPI):
    """GitHub API integration for repository and trend analysis"""

    def __init__(self, token: Optional[str] = None):
        # GitHub API rate limits: 60 / hour unauthenticated, 5000 / hour authenticated
        if token:
            rate_config = RateLimitConfig(
                requests_per_minute=80,  # Conservative for authenticated
                requests_per_hour=4000,
                requests_per_day=50000,
                burst_limit=10,
            )
        else:
            rate_config = RateLimitConfig(
                requests_per_minute=1,  # Very conservative for unauthenticated
                requests_per_hour=50,
                requests_per_day=1000,
                burst_limit=2,
            )

        super().__init__(rate_config)
        self.token = token
        self.base_url = "https://api.github.com"

        if self.token:
            self.base_headers.update(
                {
                    "Authorization": f"token {self.token}",
                    "Accept": "application / vnd.github.v3 + json",
                }
            )

    async def health_check(self) -> bool:
        """Check if GitHub API is accessible"""
        try:
            response = await self._make_request("GET", f"{self.base_url}/rate_limit")
            return "rate" in response
        except Exception as e:
            logger.error(f"GitHub health check failed: {e}")
            return False

    async def get_quota_status(self) -> Dict[str, Any]:
        """Get current quota status from GitHub API"""
        try:
            response = await self._make_request("GET", f"{self.base_url}/rate_limit")

            core_rate = response.get("rate", {})
            search_rate = response.get("resources", {}).get("search", {})

            return {
                "service": "GitHub API",
                "authenticated": bool(self.token),
                "core_limit": core_rate.get("limit", 0),
                "core_remaining": core_rate.get("remaining", 0),
                "core_reset": (
                    datetime.fromtimestamp(core_rate.get("reset", 0)).isoformat()
                    if core_rate.get("reset")
                    else None
                ),
                "search_limit": search_rate.get("limit", 0),
                "search_remaining": search_rate.get("remaining", 0),
                "search_reset": (
                    datetime.fromtimestamp(search_rate.get("reset", 0)).isoformat()
                    if search_rate.get("reset")
                    else None
                ),
                "local_daily_used": self.rate_limiter.daily_count,
                "local_hourly_used": self.rate_limiter.hourly_count,
            }
        except Exception as e:
            return {
                "service": "GitHub API",
                "error": str(e),
                "local_daily_used": self.rate_limiter.daily_count,
                "local_hourly_used": self.rate_limiter.hourly_count,
            }

    async def search_repositories(
        self,
        query: str,
        sort: str = "stars",
        order: str = "desc",
        per_page: int = 30,
        page: int = 1,
    ) -> Dict[str, Any]:
        """Search GitHub repositories"""
        await self.rate_limiter.acquire()

        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": min(per_page, 100),  # GitHub max is 100
            "page": page,
        }

        try:
            response = await self._make_request(
                "GET", f"{self.base_url}/search / repositories", params=params
            )

            repositories = []
            for repo in response.get("items", []):
                repositories.append(
                    {
                        "id": repo["id"],
                        "name": repo["name"],
                        "full_name": repo["full_name"],
                        "description": repo.get("description", ""),
                        "html_url": repo["html_url"],
                        "stars": repo["stargazers_count"],
                        "forks": repo["forks_count"],
                        "watchers": repo["watchers_count"],
                        "language": repo.get("language"),
                        "created_at": repo["created_at"],
                        "updated_at": repo["updated_at"],
                        "pushed_at": repo.get("pushed_at"),
                        "size": repo["size"],
                        "open_issues": repo["open_issues_count"],
                        "topics": repo.get("topics", []),
                        "license": (
                            repo.get("license", {}).get("name") if repo.get("license") else None
                        ),
                        "owner": {
                            "login": repo["owner"]["login"],
                            "type": repo["owner"]["type"],
                        },
                    }
                )

            return {
                "total_count": response.get("total_count", 0),
                "incomplete_results": response.get("incomplete_results", False),
                "repositories": repositories,
                "query": query,
                "page": page,
                "per_page": per_page,
            }

        except Exception as e:
            raise APIError(f"Failed to search repositories: {e}")

    async def get_trending_repositories(
        self, language: Optional[str] = None, since: str = "daily", limit: int = 30
    ) -> List[Dict[str, Any]]:
        """Get trending repositories (using search with date filters)"""
        # Calculate date range based on 'since' parameter
        now = datetime.utcnow()
        if since == "daily":
            date_filter = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        elif since == "weekly":
            date_filter = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        elif since == "monthly":
            date_filter = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        else:
            date_filter = (now - timedelta(days=1)).strftime("%Y-%m-%d")

        # Build query
        query_parts = [f"created:>{date_filter}"]
        if language:
            query_parts.append(f"language:{language}")

        query = " ".join(query_parts)

        try:
            result = await self.search_repositories(
                query=query, sort="stars", order="desc", per_page=limit
            )

            # Add trending metrics
            trending_repos = []
            for repo in result["repositories"]:
                # Calculate days since creation
                created_date = datetime.fromisoformat(repo["created_at"].replace("Z", "+00:00"))
                days_old = (now - created_date).days + 1

                # Calculate trending metrics
                stars_per_day = repo["stars"] / max(days_old, 1)
                forks_per_day = repo["forks"] / max(days_old, 1)

                trending_score = (
                    stars_per_day * 0.6
                    + forks_per_day * 0.3
                    + (repo["watchers"] / max(days_old, 1)) * 0.1
                )

                repo.update(
                    {
                        "days_old": days_old,
                        "stars_per_day": round(stars_per_day, 2),
                        "forks_per_day": round(forks_per_day, 2),
                        "trending_score": round(trending_score, 2),
                    }
                )

                trending_repos.append(repo)

            # Sort by trending score
            trending_repos.sort(key=lambda x: x["trending_score"], reverse=True)

            return trending_repos

        except Exception as e:
            raise APIError(f"Failed to get trending repositories: {e}")

    async def get_repository_details(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get detailed information about a specific repository"""
        await self.rate_limiter.acquire()

        try:
            response = await self._make_request("GET", f"{self.base_url}/repos/{owner}/{repo}")

            return {
                "id": response["id"],
                "name": response["name"],
                "full_name": response["full_name"],
                "description": response.get("description", ""),
                "html_url": response["html_url"],
                "clone_url": response["clone_url"],
                "stars": response["stargazers_count"],
                "forks": response["forks_count"],
                "watchers": response["watchers_count"],
                "language": response.get("language"),
                "languages_url": response["languages_url"],
                "created_at": response["created_at"],
                "updated_at": response["updated_at"],
                "pushed_at": response.get("pushed_at"),
                "size": response["size"],
                "open_issues": response["open_issues_count"],
                "topics": response.get("topics", []),
                "license": (
                    response.get("license", {}).get("name") if response.get("license") else None
                ),
                "default_branch": response["default_branch"],
                "network_count": response.get("network_count", 0),
                "subscribers_count": response.get("subscribers_count", 0),
                "owner": {
                    "login": response["owner"]["login"],
                    "type": response["owner"]["type"],
                    "html_url": response["owner"]["html_url"],
                },
            }

        except Exception as e:
            raise APIError(f"Failed to get repository details: {e}")

    async def get_repository_languages(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get programming languages used in a repository"""
        await self.rate_limiter.acquire()

        try:
            response = await self._make_request(
                "GET", f"{self.base_url}/repos/{owner}/{repo}/languages"
            )

            # Calculate percentages
            total_bytes = sum(response.values())
            languages = []

            for language, bytes_count in response.items():
                percentage = (bytes_count / total_bytes) * 100 if total_bytes > 0 else 0
                languages.append(
                    {
                        "language": language,
                        "bytes": bytes_count,
                        "percentage": round(percentage, 2),
                    }
                )

            # Sort by percentage
            languages.sort(key=lambda x: x["percentage"], reverse=True)

            return {
                "total_bytes": total_bytes,
                "languages": languages,
                "primary_language": languages[0]["language"] if languages else None,
            }

        except Exception as e:
            raise APIError(f"Failed to get repository languages: {e}")

    async def get_repository_contributors(
        self, owner: str, repo: str, limit: int = 30
    ) -> List[Dict[str, Any]]:
        """Get top contributors to a repository"""
        await self.rate_limiter.acquire()

        try:
            response = await self._make_request(
                "GET",
                f"{self.base_url}/repos/{owner}/{repo}/contributors",
                params={"per_page": min(limit, 100)},
            )

            contributors = []
            for contributor in response:
                contributors.append(
                    {
                        "login": contributor["login"],
                        "contributions": contributor["contributions"],
                        "html_url": contributor["html_url"],
                        "avatar_url": contributor["avatar_url"],
                        "type": contributor["type"],
                    }
                )

            return contributors

        except Exception as e:
            raise APIError(f"Failed to get repository contributors: {e}")

    async def analyze_technology_trends(
        self, technologies: List[str], time_period: str = "monthly"
    ) -> Dict[str, Any]:
        """Analyze trends for specific technologies"""
        try:
            results = {}

            for tech in technologies:
                # Search for repositories using this technology
                repo_data = await self.search_repositories(
                    query=f"language:{tech}", sort="updated", per_page=100
                )

                if repo_data["repositories"]:
                    repos = repo_data["repositories"]

                    # Calculate metrics
                    total_stars = sum(repo["stars"] for repo in repos)
                    total_forks = sum(repo["forks"] for repo in repos)
                    avg_stars = total_stars / len(repos)
                    avg_forks = total_forks / len(repos)

                    # Analyze recent activity
                    now = datetime.utcnow()
                    recent_repos = [
                        repo
                        for repo in repos
                        if datetime.fromisoformat(repo["updated_at"].replace("Z", "+00:00"))
                        > now - timedelta(days=30)
                    ]

                    activity_score = len(recent_repos) / len(repos) * 100

                    results[tech] = {
                        "total_repositories": repo_data["total_count"],
                        "analyzed_repositories": len(repos),
                        "total_stars": total_stars,
                        "total_forks": total_forks,
                        "avg_stars": round(avg_stars, 2),
                        "avg_forks": round(avg_forks, 2),
                        "recent_activity_score": round(activity_score, 2),
                        "top_repositories": repos[:5],  # Top 5 by stars
                        "trending_score": round(
                            (avg_stars * 0.4) + (avg_forks * 0.3) + (activity_score * 0.3),
                            2,
                        ),
                    }
                else:
                    results[tech] = {
                        "total_repositories": 0,
                        "error": "No repositories found",
                    }

                # Add delay between requests to respect rate limits
                await asyncio.sleep(1)

            # Rank technologies by trending score
            ranked_techs = sorted(
                [(tech, data) for tech, data in results.items() if "trending_score" in data],
                key=lambda x: x[1]["trending_score"],
                reverse=True,
            )

            return {
                "technologies": results,
                "ranked_technologies": [
                    {"technology": tech, **data} for tech, data in ranked_techs
                ],
                "analysis_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            raise APIError(f"Failed to analyze technology trends: {e}")

    async def get_user_repositories(self, username: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Get repositories for a specific user"""
        await self.rate_limiter.acquire()

        try:
            response = await self._make_request(
                "GET",
                f"{self.base_url}/users/{username}/repos",
                params={"sort": "updated", "per_page": min(limit, 100)},
            )

            repositories = []
            for repo in response:
                repositories.append(
                    {
                        "name": repo["name"],
                        "full_name": repo["full_name"],
                        "description": repo.get("description", ""),
                        "html_url": repo["html_url"],
                        "stars": repo["stargazers_count"],
                        "forks": repo["forks_count"],
                        "language": repo.get("language"),
                        "created_at": repo["created_at"],
                        "updated_at": repo["updated_at"],
                        "topics": repo.get("topics", []),
                        "private": repo["private"],
                    }
                )

            return repositories

        except Exception as e:
            raise APIError(f"Failed to get user repositories: {e}")
