# content_sources.py
from typing import Any, Dict, List

import httpx
from fastapi import APIRouter, HTTPException, Query

from shared_utils import Provider, gambling_enabled, get_secret, http_with_fallback

router = APIRouter(prefix="/content", tags=["content"])

PROVIDERS = {
    "news": [
        Provider(
            "newsapi", "NewsAPI", "https://newsapi.org", "General news aggregation"
        ),
        Provider(
            "guardian",
            "The Guardian",
            "https://open-platform.theguardian.com",
            "UK news and opinion",
        ),
        Provider(
            "nytimes",
            "New York Times",
            "https://developer.nytimes.com",
            "US news of record",
        ),
    ],
    "ai": [
        Provider(
            "arxiv", "arXiv", "https://arxiv.org", "Academic papers and preprints"
        ),
        Provider(
            "semanticscholar",
            "Semantic Scholar",
            "https://www.semanticscholar.org",
            "AI research papers",
        ),
    ],
    "wellness": [
        Provider(
            "usda",
            "USDA FoodData",
            "https://fdc.nal.usda.gov",
            "Nutritional information",
        ),
        Provider(
            "edamam",
            "Edamam",
            "https://developer.edamam.com",
            "Recipe and nutrition API",
        ),
    ],
    "sports": [
        Provider(
            "balldontlie",
            "Ball Don't Lie",
            "https://www.balldontlie.io",
            "NBA games and stats",
        ),
        Provider(
            "thesportsdb",
            "TheSportsDB",
            "https://www.thesportsdb.com",
            "Sports data and schedules",
        ),
        Provider(
            "football_data",
            "Football-Data.org",
            "https://www.football-data.org",
            "Soccer/football data",
        ),
    ],
    "finance": [
        Provider("finnhub", "Finnhub", "https://finnhub.io", "Stock market data"),
        Provider(
            "alphavantage",
            "Alpha Vantage",
            "https://www.alphavantage.co",
            "Financial data and forex",
        ),
        Provider(
            "coingecko", "CoinGecko", "https://www.coingecko.com", "Cryptocurrency data"
        ),
        Provider("coincap", "CoinCap", "https://coincap.io", "Crypto market data"),
    ],
    "weather": [
        Provider(
            "openmeteo", "Open-Meteo", "https://open-meteo.com", "Weather forecasts"
        ),
        Provider(
            "meteostat", "Meteostat", "https://meteostat.net", "Historical weather data"
        ),
        Provider(
            "weather_gov", "Weather.gov", "https://www.weather.gov", "US weather alerts"
        ),
    ],
    "geocoding": [
        Provider(
            "openmeteo_geo",
            "Open-Meteo Geocoding",
            "https://open-meteo.com",
            "Location geocoding",
        )
    ],
    "pets": [
        Provider(
            "thedogapi",
            "TheDogAPI",
            "https://api.thedogapi.com",
            "Dog breeds and images",
        ),
        Provider(
            "thecatapi",
            "TheCatAPI",
            "https://api.thecatapi.com",
            "Cat breeds and images",
        ),
        Provider(
            "petfinder",
            "Petfinder",
            "https://api.petfinder.com",
            "Pet adoption listings",
        ),
    ],
    "pets_affiliates": [
        Provider(
            "chewy",
            "Chewy",
            "https://www.chewy.com/affiliates",
            "Pet supplies affiliate program",
        ),
        Provider(
            "petco",
            "Petco",
            "https://www.petco.com/shop/en/petcostore/content/affiliate-program",
            "Pet retailer affiliate program",
        ),
        Provider(
            "petsmart",
            "PetSmart",
            "https://www.petsmart.com/help/affiliate-program/",
            "Pet store affiliate program",
        ),
        Provider(
            "rover",
            "Rover",
            "https://join.rover.com/affiliates/",
            "Pet sitting/walking affiliate program",
        ),
        Provider(
            "embark",
            "Embark Dog DNA",
            "https://www.embarkvet.com/affiliates/",
            "Dog DNA testing affiliate program",
        ),
        Provider(
            "barkbox",
            "BarkBox",
            "https://www.barkbox.com/affiliates",
            "Pet subscription box affiliate program",
        ),
    ],
    "pets_birds_data": {
        "members": ["ebird", "zoo_animal_api"],
        "strategy": "priority_round_robin",
    },
    "pets_exotics_info": {
        "members": ["fishwatch", "zoo_animal_api"],
        "strategy": "priority_round_robin",
    },
    "pets_dog_images": {
        "members": ["thedogapi", "dog_ceo"],
        "strategy": "priority_round_robin",
    },
    "pets_birds": [
        Provider(
            "ebird",
            "eBird (Bird Sightings)",
            "https://api.ebird.org/v2",
            "Bird observation and sighting data",
        )
    ],
    "pets_misc": [
        Provider(
            "zoo_animal_api",
            "Zoo Animal API (Random Animal)",
            "https://zoo-animal-api.vercel.app",
            "Random animal facts and information",
        ),
        Provider(
            "dog_ceo",
            "Dog CEO (Images/Breeds)",
            "https://dog.ceo",
            "Dog breed images and information",
        ),
    ],
    "pets_fish": [
        Provider(
            "fishwatch",
            "NOAA FishWatch (Species Info)",
            "https://www.fishwatch.gov",
            "Fish species and sustainability information",
        )
    ],
    "pets_care": [
        Provider(
            "vetster",
            "Vetster (Tele-vet)",
            "https://api.vetster.com",
            "Veterinary telemedicine services",
        ),
        Provider(
            "pawp",
            "Pawp (Tele-vet)",
            "https://api.pawp.com",
            "Online veterinary consultations",
        ),
        Provider(
            "airvet",
            "Airvet (Tele-vet)",
            "https://api.airvet.com",
            "Virtual veterinary care platform",
        ),
    ],
    "scheduling": [
        Provider(
            "calendly",
            "Calendly (Scheduling)",
            "https://api.calendly.com",
            "Appointment scheduling and calendar management",
        )
    ],
    "gambling": [
        Provider(
            "theoddsapi",
            "The Odds API",
            "https://the-odds-api.com",
            "Sports betting odds",
        ),
        Provider(
            "apisports_odds",
            "API-Sports",
            "https://rapidapi.com/api-sports",
            "Sports odds via RapidAPI",
        ),
    ],
    "birds_exotics_affiliates": {
        "members": [
            {
                "id": "tractor_supply",
                "name": "Tractor Supply (Feed/Farm/Poultry)",
                "url": "https://www.tractorsupply.com/tsc/cms/affiliate-program",
                "enabled": False,
                "status_light": "purple",
            },
            {
                "id": "only_natural_pet",
                "name": "Only Natural Pet",
                "url": "https://www.onlynaturalpet.com/pages/affiliate-program",
                "enabled": False,
                "status_light": "purple",
            },
            {
                "id": "zooplus",
                "name": "Zooplus (EU)",
                "url": "https://www.zooplus.com/info/about/affiliate",
                "enabled": False,
                "status_light": "purple",
            },
            {
                "id": "petsuppliesplus",
                "name": "Pet Supplies Plus",
                "url": "https://www.petsuppliesplus.com/our-company/affiliate-program",
                "enabled": False,
                "status_light": "purple",
            },
        ],
        "strategy": "priority_round_robin",
    },
}


# --- Politics / General news
@router.get("/news/politics")
async def politics_news(topic: str = Query("election")):
    async def do(client: httpx.AsyncClient, p):
        if p.id == "guardian":
            key = get_secret("GUARDIAN_API_KEY")
            r = await client.get(
                "https://content.guardianapis.com/search",
                params={
                    "api-key": key,
                    "q": topic,
                    "order-by": "newest",
                    "page-size": 10,
                    "show-fields": "trailText,thumbnail",
                },
            )
            r.raise_for_status()
            js = r.json()
            return [
                {"title": x["webTitle"], "url": x["webUrl"], "source": "Guardian"}
                for x in js["response"]["results"]
            ]
        if p.id == "newsapi":
            key = get_secret("NEWSAPI_KEY")
            r = await client.get(
                "https://newsapi.org/v2/everything",
                headers={"Authorization": key},
                params={
                    "q": topic,
                    "sortBy": "publishedAt",
                    "pageSize": 10,
                    "language": "en",
                },
            )
            r.raise_for_status()
            js = r.json()
            return [
                {
                    "title": a["title"],
                    "url": a["url"],
                    "source": a.get("source", {}).get("name", "NewsAPI"),
                }
                for a in js.get("articles", [])
            ]
        if p.id == "gdelt":
            # GDELT query: recent English articles with keyword
            r = await client.get(
                "https://api.gdeltproject.org/api/v2/doc/doc",
                params={
                    "query": topic,
                    "mode": "ArtList",
                    "timespan": "1d",
                    "format": "json",
                    "maxrecords": 50,
                },
            )
            r.raise_for_status()
            js = r.json()
            return [
                {"title": a["title"], "url": a["url"], "source": "GDELT"}
                for a in js.get("articles", [])
            ]
        if p.id == "hackernews":
            # HN Search by Algolia (no key)
            r = await client.get(
                "https://hn.algolia.com/api/v1/search",
                params={"query": topic, "tags": "story"},
            )
            r.raise_for_status()
            js = r.json()
            return [
                {
                    "title": h["title"],
                    "url": h["url"]
                    or f"https://news.ycombinator.com/item?id={h['objectID']}",
                    "source": "HN",
                }
                for h in js.get("hits", [])
            ]
        if p.id == "gnews":
            key = get_secret("GNEWS_KEY")
            r = await client.get(
                "https://gnews.io/api/v4/search",
                params={"q": topic, "lang": "en", "max": 10, "token": key},
            )
            r.raise_for_status()
            js = r.json()
            return [
                {"title": a["title"], "url": a["url"], "source": "GNews"}
                for a in js.get("articles", [])
            ]
        raise RuntimeError("unknown news provider")

    results = await http_with_fallback(
        "news", do, prefer=["guardian", "newsapi", "gdelt", "gnews", "hackernews"]
    )
    return {"topic": topic, "items": results}


# --- Tech news / launches
@router.get("/news/tech")
async def tech_news(topic: str = Query("gpu")):
    async def do(client: httpx.AsyncClient, p):
        if p.id == "producthunt":
            token = get_secret("PRODUCTHUNT_TOKEN")
            # PH v2 GraphQL simple search
            q = {
                "query": f'query {{ posts(order: RANKING, first: 10, query: "{topic}") {{ edges {{ node {{ name url tagline }} }} }} }}'
            }
            r = await client.post(
                "https://api.producthunt.com/v2/api/graphql",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=q,
            )
            r.raise_for_status()
            js = r.json()
            edges = js.get("data", {}).get("posts", {}).get("edges", [])
            return [
                {
                    "title": e["node"]["name"],
                    "url": e["node"]["url"],
                    "source": "ProductHunt",
                }
                for e in edges
            ]
        if p.id == "github":
            r = await client.get(
                "https://api.github.com/search/repositories",
                params={"q": topic, "sort": "stars", "order": "desc", "per_page": 10},
                headers={"Accept": "application/vnd.github+json"},
            )
            r.raise_for_status()
            js = r.json()
            return [
                {
                    "title": repo["full_name"],
                    "url": repo["html_url"],
                    "source": "GitHub",
                }
                for repo in js.get("items", [])
            ]
        if p.id == "hackernews":
            r = await client.get(
                "https://hn.algolia.com/api/v1/search",
                params={"query": topic, "tags": "story"},
            )
            r.raise_for_status()
            js = r.json()
            return [
                {
                    "title": h["title"],
                    "url": h["url"]
                    or f"https://news.ycombinator.com/item?id={h['objectID']}",
                    "source": "HN",
                }
                for h in js.get("hits", [])
            ]
        raise RuntimeError("unknown tech provider")

    results = await http_with_fallback(
        "tech", do, prefer=["producthunt", "github", "hackernews"]
    )
    return {"topic": topic, "items": results}


# --- AI papers (arXiv → PapersWithCode)
@router.get("/ai/papers")
async def ai_papers(q: str = Query("large language models")):
    async def do(client: httpx.AsyncClient, p):
        if p.id == "arxiv":
            r = await client.get(
                "https://export.arxiv.org/api/query",
                params={"search_query": f"all:{q}", "start": 0, "max_results": 10},
            )
            r.raise_for_status()
            txt = r.text
            # super-light parse (title + link)
            import re

            entries = re.findall(r"<entry>(.*?)</entry>", txt, re.S)
            out = []
            for e in entries:
                t = re.search(r"<title>(.*?)</title>", e, re.S)
                l = re.search(r"<id>(.*?)</id>", e, re.S)
                if t and l:
                    out.append(
                        {
                            "title": t.group(1).strip(),
                            "url": l.group(1).strip(),
                            "source": "arXiv",
                        }
                    )
            return out
        if p.id == "paperswithcode":
            r = await client.get(
                "https://paperswithcode.com/api/v1/search/",
                params={"q": q, "format": "json"},
            )
            r.raise_for_status()
            js = r.json()
            return [
                {
                    "title": it["paper_title"],
                    "url": it["paper_url"],
                    "source": "PapersWithCode",
                }
                for it in js.get("results", [])
            ]
        raise RuntimeError("unknown knowledge provider")

    results = await http_with_fallback(
        "knowledge", do, prefer=["arxiv", "paperswithcode", "wikimedia"]
    )
    return {"query": q, "items": results}


# --- Wellness: nutrition lookup
@router.get("/wellness/nutrition")
async def wellness_nutrition(food: str = Query("oatmeal")):
    async def do(client: httpx.AsyncClient, p):
        if p.id == "usda_fdc":
            key = get_secret("USDA_FDC_KEY")
            r = await client.get(
                "https://api.nal.usda.gov/fdc/v1/foods/search",
                params={"api_key": key, "query": food, "pageSize": 5},
            )
            r.raise_for_status()
            js = r.json()
            out = []
            for item in js.get("foods", []):
                out.append(
                    {
                        "desc": item.get("description"),
                        "brand": item.get("brandOwner"),
                        "calories": next(
                            (
                                n["value"]
                                for n in item.get("foodNutrients", [])
                                if n.get("nutrientName") == "Energy"
                            ),
                            None,
                        ),
                        "source": "USDA",
                    }
                )
            return out
        if p.id == "openfda":
            r = await client.get(
                "https://api.fda.gov/food/enforcement.json",
                params={"search": food, "limit": 5},
            )
            # openFDA returns 404 when no results; treat as empty
            if r.status_code == 404:
                return []
            r.raise_for_status()
            js = r.json()
            return [
                {
                    "desc": rec.get("reason_for_recall"),
                    "brand": rec.get("product_description"),
                    "calories": None,
                    "source": "openFDA",
                }
                for rec in js.get("results", [])
            ]
        raise RuntimeError("unknown wellness provider")

    results = await http_with_fallback("wellness", do, prefer=["usda_fdc", "openfda"])
    return {"food": food, "items": results}


# --- Sports data
@router.get("/sports")
async def sports_data(sport: str = Query("basketball")):
    async def do(client: httpx.AsyncClient, p):
        if p.id == "balldontlie":
            r = await client.get(
                "https://www.balldontlie.io/api/v1/games",
                params={"seasons[]": "2023", "per_page": 10},
            )
            r.raise_for_status()
            js = r.json()
            return [
                {
                    "title": f"{g['home_team']['full_name']} vs {g['visitor_team']['full_name']}",
                    "score": f"{g['home_team_score']}-{g['visitor_team_score']}",
                    "source": "BallDontLie",
                }
                for g in js.get("data", [])
            ]
        if p.id == "thesportsdb":
            key = get_secret("THESPORTSDB_KEY")
            r = await client.get(
                f"https://www.thesportsdb.com/api/v1/json/{key}/searchteams.php",
                params={"t": sport},
            )
            r.raise_for_status()
            js = r.json()
            return [
                {
                    "title": t["strTeam"],
                    "league": t.get("strLeague"),
                    "source": "TheSportsDB",
                }
                for t in js.get("teams", []) or []
            ]
        if p.id == "football_data":
            key = get_secret("FOOTBALL_DATA_KEY")
            r = await client.get(
                "https://api.football-data.org/v4/competitions",
                headers={"X-Auth-Token": key},
            )
            r.raise_for_status()
            js = r.json()
            return [
                {
                    "title": c["name"],
                    "area": c.get("area", {}).get("name"),
                    "source": "Football-Data",
                }
                for c in js.get("competitions", [])
            ]
        raise RuntimeError("unknown sports provider")

    results = await http_with_fallback(
        "sports", do, prefer=["balldontlie", "thesportsdb", "football_data"]
    )
    return {"sport": sport, "items": results}


# --- Finance data
@router.get("/finance")
async def finance_data(symbol: str = Query("AAPL")):
    async def do(client: httpx.AsyncClient, p):
        if p.id == "alphavantage":
            key = get_secret("ALPHAVANTAGE_KEY")
            r = await client.get(
                "https://www.alphavantage.co/query",
                params={"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": key},
            )
            r.raise_for_status()
            js = r.json()
            quote = js.get("Global Quote", {})
            return (
                [
                    {
                        "symbol": quote.get("01. symbol"),
                        "price": quote.get("05. price"),
                        "change": quote.get("09. change"),
                        "source": "AlphaVantage",
                    }
                ]
                if quote
                else []
            )
        if p.id == "finnhub":
            key = get_secret("FINNHUB_KEY")
            r = await client.get(
                "https://finnhub.io/api/v1/quote",
                params={"symbol": symbol, "token": key},
            )
            r.raise_for_status()
            js = r.json()
            return [
                {
                    "symbol": symbol,
                    "price": js.get("c"),
                    "change": js.get("d"),
                    "source": "Finnhub",
                }
            ]
        if p.id == "coingecko":
            r = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": symbol.lower(),
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                },
            )
            r.raise_for_status()
            js = r.json()
            data = js.get(symbol.lower(), {})
            return (
                [
                    {
                        "symbol": symbol,
                        "price": data.get("usd"),
                        "change": data.get("usd_24h_change"),
                        "source": "CoinGecko",
                    }
                ]
                if data
                else []
            )
        if p.id == "coincap":
            r = await client.get(f"https://api.coincap.io/v2/assets/{symbol.lower()}")
            r.raise_for_status()
            js = r.json()
            asset = js.get("data", {})
            return (
                [
                    {
                        "symbol": asset.get("symbol"),
                        "price": asset.get("priceUsd"),
                        "change": asset.get("changePercent24Hr"),
                        "source": "CoinCap",
                    }
                ]
                if asset
                else []
            )
        raise RuntimeError("unknown finance provider")

    results = await http_with_fallback(
        "finance", do, prefer=["alphavantage", "finnhub", "coingecko", "coincap"]
    )
    return {"symbol": symbol, "items": results}


# --- Weather data
@router.get("/weather")
async def weather_data(location: str = Query("New York")):
    async def do(client: httpx.AsyncClient, p):
        if p.id == "openmeteo":
            r = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": "40.7128",
                    "longitude": "-74.0060",
                    "current_weather": "true",
                },
            )
            r.raise_for_status()
            js = r.json()
            current = js.get("current_weather", {})
            return [
                {
                    "location": location,
                    "temperature": current.get("temperature"),
                    "windspeed": current.get("windspeed"),
                    "source": "OpenMeteo",
                }
            ]
        if p.id == "weather_gov":
            r = await client.get("https://api.weather.gov/points/40.7128,-74.0060")
            r.raise_for_status()
            js = r.json()
            forecast_url = js.get("properties", {}).get("forecast")
            if forecast_url:
                r2 = await client.get(forecast_url)
                r2.raise_for_status()
                js2 = r2.json()
                periods = js2.get("properties", {}).get("periods", [])
                return [
                    {
                        "location": location,
                        "forecast": p.get("detailedForecast"),
                        "temperature": p.get("temperature"),
                        "source": "Weather.gov",
                    }
                    for p in periods[:3]
                ]
            return []
        raise RuntimeError("unknown weather provider")

    results = await http_with_fallback(
        "weather", do, prefer=["openmeteo", "weather_gov"]
    )
    return {"location": location, "items": results}


# --- SPORTS: scores by league/date
@router.get("/sports/scores")
async def sports_scores(league: str = Query("nba"), date: str = Query(None)):
    async def do(client, p):
        if p.id == "balldontlie" and league.lower() == "nba":
            params = {"per_page": 50}
            if date:
                params["dates[]"] = date
            r = await client.get("https://api.balldontlie.io/v1/games", params=params)
            r.raise_for_status()
            js = r.json()
            out = []
            for g in js.get("data", []):
                out.append(
                    {
                        "league": "NBA",
                        "home": g["home_team"]["abbreviation"],
                        "away": g["visitor_team"]["abbreviation"],
                        "home_score": g["home_team_score"],
                        "away_score": g["visitor_team_score"],
                        "status": g["status"],
                        "tipoff": g["date"],
                    }
                )
            return out
        if p.id == "thesportsdb":
            key = get_secret("THESPORTSDB_KEY")
            if league.lower() in ("nba", "mlb", "nhl", "nfl"):
                # day schedule (US leagues); fallback if date unset → today
                from datetime import date as _d

                d = date or str(_d.today())
                r = await client.get(
                    f"https://www.thesportsdb.com/api/v1/json/{key}/eventsday.php",
                    params={"d": d, "s": league.upper()},
                )
                r.raise_for_status()
                js = r.json()
                out = []
                for e in js.get("events") or []:
                    out.append(
                        {
                            "league": league.upper(),
                            "home": e.get("strHomeTeam"),
                            "away": e.get("strAwayTeam"),
                            "home_score": e.get("intHomeScore"),
                            "away_score": e.get("intAwayScore"),
                            "status": e.get("strStatus"),
                            "tipoff": e.get("dateEvent"),
                        }
                    )
                return out
            raise RuntimeError("league not supported by TheSportsDB handler")
        raise RuntimeError("unknown sports provider")

    pref = ["balldontlie", "thesportsdb"]
    return {
        "league": league,
        "date": date,
        "games": await http_with_fallback("sports", do, prefer=pref),
    }


# --- SPORTS: soccer standings (EPL/LaLiga/Serie A etc.)
@router.get("/sports/standings")
async def sports_standings(comp: str = Query("PL")):
    async def do(client, p):
        if p.id == "football_data":
            key = get_secret("FOOTBALL_DATA_KEY")
            r = await client.get(
                f"https://api.football-data.org/v4/competitions/{comp}/standings",
                headers={"X-Auth-Token": key},
            )
            r.raise_for_status()
            js = r.json()
            table = []
            for s in js.get("standings", []):
                if s.get("type") == "TOTAL":
                    for t in s.get("table", []):
                        table.append(
                            {
                                "pos": t.get("position"),
                                "team": t["team"]["name"],
                                "played": t.get("playedGames"),
                                "gd": t.get("goalDifference"),
                                "points": t.get("points"),
                            }
                        )
            return table
        if p.id == "thesportsdb":
            key = get_secret("THESPORTSDB_KEY")
            # minimal: EPL season table (harder generally via TSDB; demo: last events)
            r = await client.get(
                f"https://www.thesportsdb.com/api/v1/json/{key}/latestepl.php"
            )
            if r.status_code == 404:
                return []
            r.raise_for_status()
            js = r.json()
            # Not true standings; return latest match summaries when standings unavailable
            out = [
                {
                    "recent_match": f"{m.get('strHomeTeam')} vs {m.get('strAwayTeam')}",
                    "score": m.get("intHomeScore"),
                    "score2": m.get("intAwayScore"),
                }
                for m in (js.get("teams") or [])
            ]
            return out
        raise RuntimeError("unknown sports provider")

    return {
        "competition": comp,
        "table": await http_with_fallback(
            "sports", do, prefer=["football_data", "thesportsdb"]
        ),
    }


# --- FINANCE: quotes (stocks + crypto)
@router.get("/finance/quotes")
async def finance_quotes(symbols: str = Query("AAPL,BTC")):
    syms = [s.strip().upper() for s in symbols.split(",") if s.strip()]

    async def do(client, p):
        if p.id == "finnhub":
            key = get_secret("FINNHUB_KEY")
            out = []
            for s in syms:
                r = await client.get(
                    "https://finnhub.io/api/v1/quote",
                    params={"symbol": s, "token": key},
                )
                if r.status_code == 429:
                    r.raise_for_status()
                if r.status_code == 200:
                    q = r.json()
                    out.append(
                        {
                            "symbol": s,
                            "price": q.get("c"),
                            "high": q.get("h"),
                            "low": q.get("l"),
                            "source": "Finnhub",
                        }
                    )
            return out
        if p.id == "alphavantage":
            key = get_secret("ALPHAVANTAGE_KEY")
            out = []
            for s in syms:
                func = (
                    "GLOBAL_QUOTE"
                    if "-" not in s and not s.endswith("USD")
                    else "CURRENCY_EXCHANGE_RATE"
                )
                params = {"apikey": key}
                if func == "GLOBAL_QUOTE":
                    params.update({"function": func, "symbol": s})
                else:
                    base, quote = (
                        (s.split("-")[0], s.split("-")[1])
                        if "-" in s
                        else (s.replace("USD", ""), "USD")
                    )
                    params.update(
                        {
                            "function": "CURRENCY_EXCHANGE_RATE",
                            "from_currency": base,
                            "to_currency": quote,
                        }
                    )
                r = await client.get("https://www.alphavantage.co/query", params=params)
                r.raise_for_status()
                js = r.json()
                if func == "GLOBAL_QUOTE":
                    g = js.get("Global Quote", {})
                    price = g.get("05. price")
                else:
                    g = js.get("Realtime Currency Exchange Rate", {})
                    price = g.get("5. Exchange Rate")
                out.append(
                    {
                        "symbol": s,
                        "price": float(price) if price else None,
                        "source": "AlphaVantage",
                    }
                )
            return out
        if p.id == "coingecko":
            # map crypto symbols to ids: quick fetch by symbol → id
            ids = []
            for s in syms:
                r = await client.get(
                    "https://api.coingecko.com/api/v3/search", params={"query": s}
                )
                if r.status_code == 200:
                    js = r.json()
                    cid = next(
                        (
                            c["id"]
                            for c in js.get("coins", [])
                            if c.get("symbol", "").upper() == s.upper()
                        ),
                        None,
                    )
                    if cid:
                        ids.append(cid)
            if not ids:
                return []
            r = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": ",".join(ids), "vs_currencies": "usd"},
            )
            r.raise_for_status()
            js = r.json()
            out = []
            for cid, row in js.items():
                price = row.get("usd")
                out.append({"symbol": cid, "price": price, "source": "CoinGecko"})
            return out
        if p.id == "coincap":
            out = []
            for s in syms:
                r = await client.get(
                    f"https://api.coincap.io/v2/assets", params={"search": s}
                )
                r.raise_for_status()
                js = r.json()
                if js.get("data"):
                    a = js["data"][0]
                    out.append(
                        {
                            "symbol": a["symbol"],
                            "price": float(a["priceUsd"]),
                            "source": "CoinCap",
                        }
                    )
            return out
        raise RuntimeError("unknown finance provider")

    prefer = ["finnhub", "alphavantage", "coingecko", "coincap"]
    return {
        "symbols": syms,
        "quotes": await http_with_fallback("finance", do, prefer=prefer),
    }


# --- WEATHER: geocode + forecast + US alerts
@router.get("/weather/forecast")
async def weather_forecast(
    city: str = Query(None), lat: float = Query(None), lon: float = Query(None)
):
    async def do_geo(client, p):
        if p.id == "openmeteo_geo":
            r = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 1},
            )
            r.raise_for_status()
            js = r.json()
            if not js.get("results"):
                return None
            r0 = js["results"][0]
            return r0["latitude"], r0["longitude"], r0.get("name")
        raise RuntimeError("unknown geocoder")

    if city and (lat is None or lon is None):
        latlon = await http_with_fallback("geocoding", do_geo, prefer=["openmeteo_geo"])
        if not latlon:
            raise HTTPException(404, "City not found")
        lat, lon, _ = latlon

    async def do_weather(client, p):
        if p.id == "openmeteo":
            r = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "hourly": "temperature_2m,precipitation",
                    "daily": "weathercode,temperature_2m_max,temperature_2m_min",
                    "forecast_days": 7,
                    "timezone": "auto",
                },
            )
            r.raise_for_status()
            return r.json()
        if p.id == "meteostat":
            r = await client.get(
                "https://meteostat.net/api/point/daily", params={"lat": lat, "lon": lon}
            )
            if r.status_code == 404:
                return {}
            r.raise_for_status()
            return r.json()
        raise RuntimeError("unknown weather provider")

    fc = await http_with_fallback(
        "weather", do_weather, prefer=["openmeteo", "meteostat"]
    )

    # alerts (US only)
    alerts = []

    async def do_alerts(client, p):
        if p.id == "weather_gov":
            r = await client.get(
                "https://api.weather.gov/alerts/active",
                params={"point": f"{lat},{lon}"},
            )
            if r.status_code in (404, 204):
                return []
            r.raise_for_status()
            js = r.json()
            return [
                {
                    "event": f["properties"]["event"],
                    "severity": f["properties"].get("severity"),
                    "headline": f["properties"].get("headline"),
                }
                for f in js.get("features", [])
            ]
        raise RuntimeError("unknown alerts provider")

    try:
        alerts = await http_with_fallback("weather", do_alerts, prefer=["weather_gov"])
    except Exception:
        alerts = []

    return {"lat": lat, "lon": lon, "forecast": fc, "alerts": alerts}


# --- GAMBLING/ODDS: moneylines/totals/spreads (opt-in)
@router.get("/odds/lines")
async def odds_lines(
    sport: str = Query("americanfootball_nfl"),
    regions: str = Query("us,us2"),
    markets: str = Query("h2h,spreads,totals"),
):
    if not gambling_enabled():
        raise HTTPException(
            status_code=403,
            detail="Gambling features are disabled. Enable with GAMBLING_FEATURES_ENABLED=true.",
        )

    async def do(client, p):
        if p.id == "theoddsapi":
            key = get_secret("THEODDSAPI_KEY")
            r = await client.get(
                "https://api.the-odds-api.com/v4/sports/{}/odds".format(sport),
                params={
                    "apiKey": key,
                    "regions": regions,
                    "markets": markets,
                    "oddsFormat": "american",
                },
            )
            r.raise_for_status()
            js = r.json()
            out = []
            for game in js:
                out.append(
                    {
                        "commence": game.get("commence_time"),
                        "home": game.get("home_team"),
                        "away": game.get("away_team"),
                        "books": [
                            {
                                "book": b.get("bookmaker"),
                                "h2h": next(
                                    (
                                        m["outcomes"]
                                        for m in b.get("markets", [])
                                        if m["key"] == "h2h"
                                    ),
                                    None,
                                ),
                                "spreads": next(
                                    (
                                        m["outcomes"]
                                        for m in b.get("markets", [])
                                        if m["key"] == "spreads"
                                    ),
                                    None,
                                ),
                                "totals": next(
                                    (
                                        m["outcomes"]
                                        for m in b.get("markets", [])
                                        if m["key"] == "totals"
                                    ),
                                    None,
                                ),
                            }
                            for b in game.get("bookmakers", [])
                        ],
                    }
                )
            return out
        if p.id == "apisports_odds":
            key = get_secret("RAPIDAPI_KEY")
            # demo: API-FOOTBALL odds (soccer) using RapidAPI headers
            r = await client.get(
                "https://api-football-v1.p.rapidapi.com/v3/odds",
                headers={
                    "X-RapidAPI-Key": key,
                    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com",
                },
                params={"date": "2024-08-01"},
            )  # adjust as needed
            r.raise_for_status()
            js = r.json()
            # normalize minimally
            out = []
            for r0 in js.get("response", []):
                fixture = r0.get("fixture", {})
                bks = r0.get("bookmakers", [])
                out.append(
                    {
                        "commence": fixture.get("date"),
                        "home": None,
                        "away": None,
                        "books": [
                            {
                                "book": b.get("name"),
                                "bets": [bet.get("name") for bet in b.get("bets", [])],
                            }
                            for b in bks
                        ],
                    }
                )
            return out
        raise RuntimeError("unknown odds provider")

    return {
        "sport": sport,
        "regions": regions,
        "markets": markets,
        "lines": await http_with_fallback(
            "gambling", do, prefer=["theoddsapi", "apisports_odds"]
        ),
    }


# --- Gambling odds
@router.get("/gambling/odds")
async def gambling_odds(sport: str = Query("americanfootball_nfl")):
    # Check if gambling features are enabled
    if not gambling_enabled():
        raise HTTPException(
            status_code=403, detail="Gambling features are not enabled on this instance"
        )

    async def do(client: httpx.AsyncClient, p):
        if p.id == "theoddsapi":
            key = get_secret("THEODDSAPI_KEY")
            r = await client.get(
                "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds",
                params={"apiKey": key, "regions": "us", "markets": "h2h"},
            )
            r.raise_for_status()
            js = r.json()
            return [
                {
                    "game": f"{g['home_team']} vs {g['away_team']}",
                    "commence_time": g.get("commence_time"),
                    "bookmakers": len(g.get("bookmakers", [])),
                    "source": "TheOddsAPI",
                }
                for g in js[:5]
            ]
        raise RuntimeError("unknown gambling provider")

    results = await http_with_fallback("gambling", do, prefer=["theoddsapi"])
    return {
        "sport": sport,
        "items": results,
        "disclaimer": "Gambling odds are for informational purposes only. Please gamble responsibly.",
    }


# --- Pets endpoints
@router.get("/pets/dogs/breeds")
async def get_dog_breeds(limit: int = Query(10)):
    """Get dog breeds from TheDogAPI"""

    async def do(client: httpx.AsyncClient, p):
        if p.id == "thedogapi":
            headers = {}
            key = get_secret("DOG_API_KEY")
            if key:
                headers["x-api-key"] = key
            r = await client.get(
                f"https://api.thedogapi.com/v1/breeds?limit={limit}", headers=headers
            )
            r.raise_for_status()
            js = r.json()
            return [
                {
                    "id": breed.get("id"),
                    "name": breed.get("name"),
                    "temperament": breed.get("temperament"),
                    "life_span": breed.get("life_span"),
                    "source": "TheDogAPI",
                }
                for breed in js
            ]
        raise RuntimeError("unknown pets provider")

    results = await http_with_fallback("pets", do, prefer=["thedogapi"])
    return {"limit": limit, "breeds": results}


@router.get("/pets/dogs/images")
async def get_dog_images(breed_id: str = Query(None), limit: int = Query(1)):
    """Get random dog images from TheDogAPI"""

    async def do(client: httpx.AsyncClient, p):
        if p.id == "thedogapi":
            headers = {}
            key = get_secret("DOG_API_KEY")
            if key:
                headers["x-api-key"] = key
            params = {"limit": limit}
            if breed_id:
                params["breed_ids"] = breed_id
            r = await client.get(
                "https://api.thedogapi.com/v1/images/search",
                params=params,
                headers=headers,
            )
            r.raise_for_status()
            js = r.json()
            return [
                {
                    "id": img.get("id"),
                    "url": img.get("url"),
                    "width": img.get("width"),
                    "height": img.get("height"),
                    "source": "TheDogAPI",
                }
                for img in js
            ]
        raise RuntimeError("unknown pets provider")

    results = await http_with_fallback("pets", do, prefer=["thedogapi"])
    return {"breed_id": breed_id, "limit": limit, "images": results}


@router.get("/pets/cats/breeds")
async def get_cat_breeds(limit: int = Query(10)):
    """Get cat breeds from TheCatAPI"""

    async def do(client: httpx.AsyncClient, p):
        if p.id == "thecatapi":
            headers = {}
            key = get_secret("CAT_API_KEY")
            if key:
                headers["x-api-key"] = key
            r = await client.get(
                f"https://api.thecatapi.com/v1/breeds?limit={limit}", headers=headers
            )
            r.raise_for_status()
            js = r.json()
            return [
                {
                    "id": breed.get("id"),
                    "name": breed.get("name"),
                    "temperament": breed.get("temperament"),
                    "life_span": breed.get("life_span"),
                    "source": "TheCatAPI",
                }
                for breed in js
            ]
        raise RuntimeError("unknown pets provider")

    results = await http_with_fallback("pets", do, prefer=["thecatapi"])
    return {"limit": limit, "breeds": results}


@router.get("/pets/cats/images")
async def get_cat_images(breed_id: str = Query(None), limit: int = Query(1)):
    """Get random cat images from TheCatAPI"""

    async def do(client: httpx.AsyncClient, p):
        if p.id == "thecatapi":
            headers = {}
            key = get_secret("CAT_API_KEY")
            if key:
                headers["x-api-key"] = key
            params = {"limit": limit}
            if breed_id:
                params["breed_ids"] = breed_id
            r = await client.get(
                "https://api.thecatapi.com/v1/images/search",
                params=params,
                headers=headers,
            )
            r.raise_for_status()
            js = r.json()
            return [
                {
                    "id": img.get("id"),
                    "url": img.get("url"),
                    "width": img.get("width"),
                    "height": img.get("height"),
                    "source": "TheCatAPI",
                }
                for img in js
            ]
        raise RuntimeError("unknown pets provider")

    results = await http_with_fallback("pets", do, prefer=["thecatapi"])
    return {"breed_id": breed_id, "limit": limit, "images": results}


@router.get("/pets/adoptions")
async def get_pet_adoptions(
    animal_type: str = Query("dog"),
    location: str = Query("10001"),
    limit: int = Query(20),
):
    """Get pet adoption listings from Petfinder (requires OAuth)"""

    async def do(client: httpx.AsyncClient, p):
        if p.id == "petfinder":
            token = get_secret("PETFINDER_ACCESS_TOKEN")
            if not token:
                raise RuntimeError("Petfinder access token not configured")
            headers = {"Authorization": f"Bearer {token}"}
            params = {"type": animal_type, "location": location, "limit": limit}
            r = await client.get(
                "https://api.petfinder.com/v2/animals", params=params, headers=headers
            )
            r.raise_for_status()
            js = r.json()
            return [
                {
                    "id": animal.get("id"),
                    "name": animal.get("name"),
                    "type": animal.get("type"),
                    "breed": animal.get("breeds", {}).get("primary"),
                    "age": animal.get("age"),
                    "gender": animal.get("gender"),
                    "url": animal.get("url"),
                    "source": "Petfinder",
                }
                for animal in js.get("animals", [])
            ]
        raise RuntimeError("unknown pets provider")

    results = await http_with_fallback("pets", do, prefer=["petfinder"])
    return {
        "animal_type": animal_type,
        "location": location,
        "limit": limit,
        "adoptions": results,
    }


@router.get("/pets/affiliates")
async def get_pets_affiliates(
    category: str = Query(None), enabled_only: bool = Query(False)
):
    """Get pets affiliate program information"""
    try:
        providers = PROVIDERS["pets_affiliates"]

        # Filter providers based on parameters
        filtered_providers = []
        for provider in providers:
            if enabled_only and not getattr(provider, "enabled", True):
                continue

            # Category filtering logic
            if category:
                provider_categories = {
                    "supplies": ["chewy", "petco", "petsmart", "barkbox"],
                    "services": ["rover"],
                    "health": ["embark"],
                }
                if provider.id not in provider_categories.get(category, []):
                    continue

            filtered_providers.append(provider)

        # Format response
        affiliate_programs = []
        for provider in filtered_providers:
            program_info = {
                "id": provider.id,
                "name": provider.name,
                "url": provider.base_url,
                "description": provider.description,
                "category": (
                    "supplies"
                    if provider.id in ["chewy", "petco", "petsmart", "barkbox"]
                    else "services" if provider.id == "rover" else "health"
                ),
            }
            affiliate_programs.append(program_info)

        return {
            "status": "success",
            "data": affiliate_programs,
            "count": len(affiliate_programs),
            "filters": {"category": category, "enabled_only": enabled_only},
            "categories": ["supplies", "services", "health"],
        }

    except Exception as e:
        return {
            "status": "error",
            "message": "Failed to fetch pets affiliate programs",
            "error": str(e),
        }


# --- Birds endpoints
@router.get("/pets/birds/nearby")
async def birds_nearby(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_km: int = Query(25, ge=1, le=50),
):
    # eBird if token present
    token = get_secret("EBIRD_API_TOKEN")
    if token:
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.get(
                "https://api.ebird.org/v2/data/obs/geo/recent",
                params={"lat": lat, "lng": lng, "dist": radius_km},
                headers={"X-eBirdApiToken": token},
            )
            if r.status_code < 400:
                return {"provider": "ebird", "data": r.json()}
    # Fallback static bird data
    return {
        "provider": "static",
        "data": [
            {
                "speciesCode": "amecro",
                "comName": "American Crow",
                "sciName": "Corvus brachyrhynchos",
                "locName": "Central Park, New York",
                "obsDt": "2024-01-15 10:30",
                "howMany": 3,
            },
            {
                "speciesCode": "norcrd",
                "comName": "Northern Cardinal",
                "sciName": "Cardinalis cardinalis",
                "locName": "Bryant Park, New York",
                "obsDt": "2024-01-15 09:45",
                "howMany": 2,
            },
            {
                "speciesCode": "blujay",
                "comName": "Blue Jay",
                "sciName": "Cyanocitta cristata",
                "locName": "Washington Square Park, New York",
                "obsDt": "2024-01-15 11:15",
                "howMany": 1,
            },
        ],
    }


@router.get("/pets/birds/sightings")
async def get_bird_sightings(region: str = Query("US"), limit: int = Query(10)):
    """Get recent bird sightings from eBird API"""

    async def do(client: httpx.AsyncClient, p):
        if p.id == "ebird":
            headers = {}
            key = get_secret("EBIRD_API_TOKEN")
            if key:
                headers["X-eBirdApiToken"] = key
            else:
                raise RuntimeError("eBird API token required")
            r = await client.get(
                f"https://api.ebird.org/v2/data/obs/{region}/recent?back=7&maxResults={limit}",
                headers=headers,
            )
            r.raise_for_status()
            js = r.json()
            return [
                {
                    "species": obs.get("comName"),
                    "scientific_name": obs.get("sciName"),
                    "location": obs.get("locName"),
                    "date": obs.get("obsDt"),
                    "count": obs.get("howMany"),
                    "source": "eBird",
                }
                for obs in js
            ]
        raise RuntimeError("unknown birds provider")

    results = await http_with_fallback("pets_birds", do, prefer=["ebird"])
    return {"region": region, "limit": limit, "sightings": results}


# --- Fish endpoints
@router.get("/pets/fish/species")
async def fish_species(limit: int = Query(50, ge=1, le=500)):
    # FishWatch API is no longer available, using static fallback data
    static_fish_data = [
        {
            "name": "Atlantic Salmon",
            "scientific": "Salmo salar",
            "biology": "Atlantic salmon are anadromous fish, meaning they are born in fresh water, migrate to the ocean, and return to fresh water to reproduce. They can live up to 8 years and grow to 30 inches long.",
            "habitat": "North Atlantic Ocean and rivers that flow into it. Prefer cold, clean water with high oxygen levels.",
        },
        {
            "name": "Pacific Cod",
            "scientific": "Gadus macrocephalus",
            "biology": "Pacific cod are bottom-dwelling fish that can live up to 18 years. They feed on invertebrates and smaller fish, and can grow up to 3 feet in length.",
            "habitat": "North Pacific Ocean, from the Bering Sea to California. Found in depths from 30 to 1,200 feet.",
        },
        {
            "name": "Yellowfin Tuna",
            "scientific": "Thunnus albacares",
            "biology": "Yellowfin tuna are fast-swimming pelagic fish that can reach speeds of 50 mph. They can live up to 7 years and grow to over 6 feet long.",
            "habitat": "Tropical and subtropical waters worldwide. Prefer open ocean environments with temperatures above 15°C.",
        },
        {
            "name": "Red Snapper",
            "scientific": "Lutjanus campechanus",
            "biology": "Red snapper are long-lived fish that can live over 50 years. They are opportunistic feeders and important both commercially and recreationally.",
            "habitat": "Gulf of Mexico and southeastern Atlantic coast. Found near reefs and rocky bottoms in depths of 30-620 feet.",
        },
        {
            "name": "Mahi-Mahi",
            "scientific": "Coryphaena hippurus",
            "biology": "Mahi-mahi are fast-growing fish with a lifespan of 4-5 years. They are excellent swimmers and known for their acrobatic abilities when caught.",
            "habitat": "Warm waters of tropical and subtropical seas worldwide. Prefer surface waters and often found near floating debris.",
        },
    ]

    # Apply limit to the static data
    limited_data = static_fish_data[: min(limit, len(static_fish_data))]

    return {
        "provider": "static_fallback",
        "count": len(limited_data),
        "species": limited_data,
    }


# --- Random animal facts endpoint
@router.get("/pets/random")
async def get_random_animal(limit: int = Query(1)):
    """Get random animal facts from Zoo Animal API or Dog CEO"""

    async def do(client: httpx.AsyncClient, p):
        if p.id == "zoo_animal_api":
            animals = []
            for _ in range(limit):
                try:
                    r = await client.get(
                        "https://zoo-animal-api.vercel.app/api/animals/rand"
                    )
                    r.raise_for_status()
                    js = r.json()
                    animals.append(
                        {
                            "name": js.get("name"),
                            "latin_name": js.get("latin_name"),
                            "habitat": js.get("habitat"),
                            "diet": js.get("diet"),
                            "source": "Zoo Animal API",
                        }
                    )
                except:
                    break
            return animals
        elif p.id == "dog_ceo":
            r = await client.get(f"https://dog.ceo/api/breeds/image/random/{limit}")
            r.raise_for_status()
            js = r.json()
            if js.get("status") == "success":
                images = js.get("message", [])
                if isinstance(images, str):
                    images = [images]
                return [
                    {"type": "dog", "image_url": img, "source": "Dog CEO"}
                    for img in images
                ]
            return []
        raise RuntimeError("unknown random animal provider")

    results = await http_with_fallback(
        "pets_misc", do, prefer=["zoo_animal_api", "dog_ceo"]
    )
    return {"limit": limit, "animals": results}


# --- Veterinary care endpoints
@router.get("/pets/care/providers")
async def get_vet_providers():
    """Get available veterinary care providers"""
    try:
        providers = PROVIDERS["pets_care"]
        care_providers = []
        for provider in providers:
            provider_info = {
                "id": provider.id,
                "name": provider.name,
                "url": provider.base_url,
                "description": provider.description,
                "type": "telemedicine",
            }
            care_providers.append(provider_info)

        return {
            "status": "success",
            "providers": care_providers,
            "count": len(care_providers),
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "Failed to fetch veterinary care providers",
            "error": str(e),
        }


# --- Scheduling endpoint
@router.get("/scheduling/availability")
async def get_scheduling_info():
    """Get scheduling service information"""
    try:
        providers = PROVIDERS["scheduling"]
        scheduling_services = []
        for provider in providers:
            service_info = {
                "id": provider.id,
                "name": provider.name,
                "url": provider.base_url,
                "description": provider.description,
                "features": [
                    "appointment_booking",
                    "calendar_integration",
                    "automated_reminders",
                ],
            }
            scheduling_services.append(service_info)

        return {
            "status": "success",
            "services": scheduling_services,
            "count": len(scheduling_services),
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "Failed to fetch scheduling services",
            "error": str(e),
        }


@router.get("/pets/affiliates/{affiliate_id}")
async def get_pets_affiliate_details(affiliate_id: str):
    """Get detailed information about a specific pets affiliate program"""
    try:
        providers = PROVIDERS["pets_affiliates"]

        # Find the provider by ID
        provider = None
        for p in providers:
            if p.id == affiliate_id:
                provider = p
                break

        if not provider:
            return {
                "status": "error",
                "message": f"Affiliate program '{affiliate_id}' not found",
                "available_programs": [p.id for p in providers],
            }

        # Enhanced program details
        program_details = {
            "id": provider.id,
            "name": provider.name,
            "url": provider.base_url,
            "description": provider.description,
        }

        # Add specific program information
        if affiliate_id == "chewy":
            program_details.update(
                {
                    "network": "Impact/Commission Junction",
                    "commission_varies_by_region": True,
                    "products": ["pet food", "supplies", "medications", "toys"],
                }
            )
        elif affiliate_id == "barkbox":
            program_details.update(
                {
                    "commission_rates": {
                        "BarkBox": "$20 per sign-up",
                        "Super Chewer": "$25 per sign-up",
                        "Other products": "$18 per item",
                    },
                    "application_review_time": "3-5 business days",
                    "contact": "affiliate@barkbox.com",
                }
            )
        elif affiliate_id == "embark":
            program_details.update(
                {
                    "commission_rate": "Up to 10% commission",
                    "programs": ["Content & creator", "Shelter/rescue", "Breeder"],
                    "products": ["DNA tests", "health screenings", "supplements"],
                }
            )

        return {"status": "success", "data": program_details}

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to fetch details for affiliate program '{affiliate_id}'",
            "error": str(e),
        }
