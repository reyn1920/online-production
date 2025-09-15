from fastapi import APIRouter
from typing import Dict, List, Any

router = APIRouter(prefix="/content", tags=["content"])

# Simple content sources configuration
CONTENT_SOURCES = {
    "sports": [
        {
            "name": "Ball Don't Lie",
            "url": "https://www.balldontlie.io",
            "description": "NBA games and stats"
        },
        {
            "name": "TheSportsDB",
            "url": "https://www.thesportsdb.com",
            "description": "Sports data and schedules"
        }
    ],
    "news": [
        {
            "name": "NewsAPI",
            "url": "https://newsapi.org",
            "description": "News articles and headlines"
        }
    ]
}

@router.get("/sources")
async def get_content_sources() -> Dict[str, List[Dict[str, Any]]]:
    """Get available content sources"""
    return CONTENT_SOURCES

@router.get("/sources/{category}")
async def get_sources_by_category(category: str) -> List[Dict[str, Any]]:
    """Get content sources by category"""
    return CONTENT_SOURCES.get(category, [])