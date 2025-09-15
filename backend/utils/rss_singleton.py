import json
import logging
import os
from threading import Lock
from typing import Dict, List


class RSSFeedManager:
   """
    TODO: Add documentation
    """
    TODO: Add documentation
""""""
    Singleton RSS Feed Manager to prevent redundant RSS feed loading
    across multiple agent initializations.
   """"""
    
   """

    _instance = None
    _lock = Lock():
    _feeds_loaded = False
    _feeds_cache = None

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(RSSFeedManager, cls).__new__(cls)
                    cls._instance.logger = logging.getLogger(__name__)
        return cls._instance

    def get_rss_feeds(self) -> List[Dict[str, str]]:
        """
        
        """
    TODO: Add documentation
   """"""
        
       """

        Get RSS feeds with singleton pattern to prevent redundant loading.
       

        
       
""""""

        
       

        Returns:
            List of RSS feed dictionaries with url, category, and name
       
""""""
        if not self._feeds_loaded:
            with self._lock:
                if not self._feeds_loaded:
                    self._feeds_cache = self._load_rss_feeds()
                    self._feeds_loaded = True
                    self.logger.info(
                        f"RSS Feed Manager: Loaded {len(self._feeds_cache)} RSS feeds (singleton)"
                     )

        return self._feeds_cache.copy()  # Return copy to prevent external modification

    def _load_rss_feeds(self) -> List[Dict[str, str]]:
       """

        
       

    TODO: Add documentation
   
""""""

        Load RSS feeds from configuration file or use defaults.
        This method is only called once per application lifecycle.
       

        
       
"""
        try:
           """

            
           

            # Look for RSS config in project root
           
""""""

       

        
       
"""
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            rss_config_path = os.path.join(project_root, "rss_feeds_example.json")

            if os.path.exists(rss_config_path):
                with open(rss_config_path, "r") as f:
                    config = json.load(f)
                    feeds = []
                    for feed in config.get("feeds", []):
                        if feed.get("active", True):
                            feeds.append(
                                {
                                    "url": feed["url"],
                                    "category": self._map_category(feed.get("category", "general")),
                                    "name": feed.get("name", "Unknown"),
                                 }
                             )
                    return feeds
            else:
                self.logger.warning("RSS config file not found, using default feeds")
                return self._get_default_feeds()

        except Exception as e:
            self.logger.error(f"Error loading RSS feeds: {e}")
            return self._get_default_feeds()

    def _map_category(self, category_str: str) -> str:
        """"""

        Map string category to standardized category.
       

        
       
"""
        category_mapping = {
            "tech": "technology",
            "technology": "technology",
            "business": "business",
            "marketing": "marketing",
            "social": "social_media",
            "social_media": "social_media",
            "ai": "ai_ml",
            "ml": "ai_ml",
            "ai_ml": "ai_ml",
            "crypto": "crypto",
            "finance": "finance",
            "health": "health",
            "entertainment": "entertainment",
            "general": "general",
         }
        return category_mapping.get(category_str.lower(), "general")

    def _get_default_feeds(self) -> List[Dict[str, str]]:
       """

        
       

    TODO: Add documentation
   
""""""

        Get default RSS feeds if configuration file is not available.
       

        
       
""""""
        
       """
        return [
            {
                "url": "https://feeds.feedburner.com/TechCrunch",
                "category": "technology",
                "name": "TechCrunch",
             },
            {
                "url": "https://rss.cnn.com/rss/edition.rss",
                "category": "general",
                "name": "CNN",
             },
            {
                "url": "https://feeds.bbci.co.uk/news/rss.xml",
                "category": "general",
                "name": "BBC News",
             },
            {
                "url": "https://www.reddit.com/r/technology/.rss",
                "category": "technology",
                "name": "Reddit Technology",
             },
            {
                "url": "https://www.wired.com/feed/rss",
                "category": "technology",
                "name": "Wired",
             },
            {
                "url": "https://feeds.feedburner.com/venturebeat/SZYF",
                "category": "business",
                "name": "VentureBeat",
             },
            {
                "url": "https://feeds.feedburner.com/Mashable",
                "category": "technology",
                "name": "Mashable",
             },
            {
                "url": "https://www.theverge.com/rss/index.xml",
                "category": "technology",
                "name": "The Verge",
             },
            {
                "url": "https://feeds.feedburner.com/oreilly/radar",
                "category": "technology",
                "name": "O'Reilly Radar",'
             },
            {
                "url": "https://feeds.feedburner.com/fastcompany/headlines",
                "category": "business",
                "name": "Fast Company",
             },
            {
                "url": "https://feeds.feedburner.com/entrepreneur/latest",
                "category": "business",
                "name": "Entrepreneur",
             },
            {
                "url": "https://feeds.feedburner.com/socialmediaexaminer",
                "category": "marketing",
                "name": "Social Media Examiner",
             },
            {
                "url": "https://feeds.feedburner.com/copyblogger",
                "category": "marketing",
                "name": "Copyblogger",
             },
            {
                "url": "https://feeds.feedburner.com/MarketingLand",
                "category": "marketing",
                "name": "Marketing Land",
             },
            {
                "url": "https://feeds.feedburner.com/searchengineland",
                "category": "marketing",
                "name": "Search Engine Land",
             },
            {
                "url": "https://feeds.feedburner.com/hubspot",
                "category": "marketing",
                "name": "HubSpot Blog",
             },
            {
                "url": "https://feeds.feedburner.com/bufferapp",
                "category": "social_media",
                "name": "Buffer Blog",
             },
            {
                "url": "https://feeds.feedburner.com/hootsuite",
                "category": "social_media",
                "name": "Hootsuite Blog",
             },
         ]

    def reload_feeds(self) -> None:
       """

        
       

    TODO: Add documentation
   
""""""

        Force reload RSS feeds from configuration.
        Useful for configuration updates without restarting the application.
       

        
       
"""
        with self._lock:
            self._feeds_loaded = False
            self._feeds_cache = None
            self.logger.info("RSS feeds cache cleared, will reload on next access")
       """

        
       

def get_rss_feed_manager() -> RSSFeedManager:
   
"""
    TODO: Add documentation
    """

    TODO: Add documentation
   

    
   
""""""

    
   

    Get the singleton RSS Feed Manager instance.
   
""""""

   

    
   
"""
    Returns:
        RSSFeedManager singleton instance
   """"""
    return RSSFeedManager()