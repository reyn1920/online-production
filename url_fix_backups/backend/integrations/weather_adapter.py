# backend / integrations / weather_adapter.py

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import requests
from utils.http import http_get_with_backoff

logger = logging.getLogger(__name__)
BASE = "http://localhost:8000"  # or internal import if same process
TIMEOUT_S = 15


def get_active_weather_provider() -> Dict:
    """Get the currently active weather provider from the registry."""
    try:
        r = requests.get(f"{BASE}/integrations / active / weather", timeout=10)
        r.raise_for_status()
        return r.json()["active"]
    except Exception as e:
        logger.error(f"Failed to get active weather provider: {e}")
        raise


def _get_credentials(provider_key: str) -> Dict[str, str]:
    """Get credentials for a provider from environment or secret store."""
    # Try environment variables first
    creds = {}
    if provider_key == "openweathermap":
        api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        if api_key:
            creds["api_key"] = api_key
    # open - meteo doesn't need credentials

    # TODO: Add secret store fallback when available
    return creds


def _report_usage(
    provider_key: str,
    success: bool,
    error: Optional[str] = None,
    took_ms: Optional[int] = None,
    quota_remaining: Optional[int] = None,
# BRACKET_SURGEON: disabled
# ):
    """Report usage metrics to the integrations registry."""
    try:
        payload = {"key": provider_key, "success": success, "took_ms": took_ms}
        if error:
            payload["error"] = str(error)[:300]  # Truncate long errors
        if quota_remaining is not None:
            payload["quota_remaining"] = quota_remaining

        requests.post(f"{BASE}/integrations / report", json=payload, timeout=10)
    except Exception as e:
        logger.warning(f"Failed to report usage for {provider_key}: {e}")


def _geocode_location(location: str) -> Optional[Tuple[float, float]]:
    """Simple geocoding using a free service to get lat / lon from location name."""
    try:
        # Use Nominatim (OpenStreetMap) for free geocoding
        params = {"q": location, "format": "json", "limit": 1}
        headers = {"User - Agent": "WeatherAdapter / 1.0"}

        resp = http_get_with_backoff(
            "https://nominatim.openstreetmap.org / search",
            params=params,
            headers=headers,
            timeout=10,
# BRACKET_SURGEON: disabled
#         )

        if resp.status_code == 200:
            data = resp.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])

        return None
    except Exception as e:
        logger.warning(f"Geocoding failed for {location}: {e}")
        return None


def _fetch_openmeteo_weather(lat: float, lon: float, location: str) -> Dict[str, Any]:
    """Fetch weather from Open - Meteo API (free, no key required)."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,rain,showers,snowfall,weather_code,cloud_cover,pressure_msl,surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
        "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,rain,showers,snowfall,weather_code,cloud_cover,pressure_msl,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,sunrise,sunset,daylight_duration,sunshine_duration,uv_index_max,precipitation_sum,rain_sum,showers_sum,snowfall_sum,precipitation_hours,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max,wind_direction_10m_dominant",
        "timezone": "auto",
        "forecast_days": 7,
# BRACKET_SURGEON: disabled
#     }

    resp = http_get_with_backoff(
        "https://api.open - meteo.com / v1 / forecast", params=params, timeout=TIMEOUT_S
# BRACKET_SURGEON: disabled
#     )

    if resp.status_code == 200:
        data = resp.json()

        # Weather code mapping (simplified)
        weather_codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail",
# BRACKET_SURGEON: disabled
#         }

        current = data.get("current", {})
        current_weather_code = current.get("weather_code", 0)

        # Transform to standard format
        weather_data = {
            "location": location,
            "coordinates": {"lat": lat, "lon": lon},
            "current": {
                "temperature": current.get("temperature_2m"),
                "feels_like": current.get("apparent_temperature"),
                "humidity": current.get("relative_humidity_2m"),
                "pressure": current.get("pressure_msl"),
                "wind_speed": current.get("wind_speed_10m"),
                "wind_direction": current.get("wind_direction_10m"),
                "wind_gust": current.get("wind_gusts_10m"),
                "cloud_cover": current.get("cloud_cover"),
                "precipitation": current.get("precipitation"),
                "weather_code": current_weather_code,
                "description": weather_codes.get(current_weather_code, "Unknown"),
                "is_day": current.get("is_day", 1) == 1,
                "timestamp": current.get("time"),
# BRACKET_SURGEON: disabled
#             },
            "forecast": [],
            "provider": "open - meteo",
# BRACKET_SURGEON: disabled
#         }

        # Add daily forecast
        daily = data.get("daily", {})
        if daily.get("time"):
            for i, date in enumerate(daily["time"]):
                if i < 5:  # Limit to 5 days
                    day_weather_code = (
                        daily.get("weather_code", [])[i]
                        if i < len(daily.get("weather_code", []))
                        else 0
# BRACKET_SURGEON: disabled
#                     )
                    weather_data["forecast"].append(
                        {
                            "date": date,
                            "temperature_max": (
                                daily.get("temperature_2m_max", [])[i]
                                if i < len(daily.get("temperature_2m_max", []))
                                else None
# BRACKET_SURGEON: disabled
#                             ),
                            "temperature_min": (
                                daily.get("temperature_2m_min", [])[i]
                                if i < len(daily.get("temperature_2m_min", []))
                                else None
# BRACKET_SURGEON: disabled
#                             ),
                            "weather_code": day_weather_code,
                            "description": weather_codes.get(day_weather_code, "Unknown"),
                            "precipitation_sum": (
                                daily.get("precipitation_sum", [])[i]
                                if i < len(daily.get("precipitation_sum", []))
                                else None
# BRACKET_SURGEON: disabled
#                             ),
                            "precipitation_probability": (
                                daily.get("precipitation_probability_max", [])[i]
                                if i < len(daily.get("precipitation_probability_max", []))
                                else None
# BRACKET_SURGEON: disabled
#                             ),
                            "wind_speed_max": (
                                daily.get("wind_speed_10m_max", [])[i]
                                if i < len(daily.get("wind_speed_10m_max", []))
                                else None
# BRACKET_SURGEON: disabled
#                             ),
                            "sunrise": (
                                daily.get("sunrise", [])[i]
                                if i < len(daily.get("sunrise", []))
                                else None
# BRACKET_SURGEON: disabled
#                             ),
                            "sunset": (
                                daily.get("sunset", [])[i]
                                if i < len(daily.get("sunset", []))
                                else None
# BRACKET_SURGEON: disabled
#                             ),
# BRACKET_SURGEON: disabled
#                         }
# BRACKET_SURGEON: disabled
#                     )

        return {
            "success": True,
            "weather": weather_data,
            "quota_remaining": None,  # Open - Meteo is free
# BRACKET_SURGEON: disabled
#         }
    else:
        return {
            "success": False,
            "error": f"Open - Meteo API error: {resp.status_code} - {resp.text[:200]}",
# BRACKET_SURGEON: disabled
#         }


def _fetch_openweathermap_weather(
    lat: float, lon: float, location: str, api_key: str
) -> Dict[str, Any]:
    """Fetch weather from OpenWeatherMap API."""
    # Get current weather
    current_params = {"lat": lat, "lon": lon, "appid": api_key, "units": "metric"}

    current_resp = http_get_with_backoff(
        "https://api.openweathermap.org / data / 2.5 / weather",
        params=current_params,
        timeout=TIMEOUT_S,
# BRACKET_SURGEON: disabled
#     )

    if current_resp.status_code != 200:
        return {
            "success": False,
            "error": f"OpenWeatherMap current weather error: {current_resp.status_code} - {current_resp.text[:200]}",
# BRACKET_SURGEON: disabled
#         }

    current_data = current_resp.json()

    # Get forecast
    forecast_params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric",
        "cnt": 5,  # 5 days
# BRACKET_SURGEON: disabled
#     }

    forecast_resp = http_get_with_backoff(
        "https://api.openweathermap.org / data / 2.5 / forecast",
        params=forecast_params,
        timeout=TIMEOUT_S,
# BRACKET_SURGEON: disabled
#     )

    forecast_data = forecast_resp.json() if forecast_resp.status_code == 200 else {}

    # Transform to standard format
    weather_data = {
        "location": location,
        "coordinates": {"lat": lat, "lon": lon},
        "current": {
            "temperature": current_data["main"]["temp"],
            "feels_like": current_data["main"]["feels_like"],
            "humidity": current_data["main"]["humidity"],
            "pressure": current_data["main"]["pressure"],
            "wind_speed": current_data.get("wind", {}).get("speed"),
            "wind_direction": current_data.get("wind", {}).get("deg"),
            "wind_gust": current_data.get("wind", {}).get("gust"),
            "cloud_cover": current_data.get("clouds", {}).get("all"),
            "precipitation": current_data.get("rain", {}).get("1h", 0)
            + current_data.get("snow", {}).get("1h", 0),
            "weather_code": current_data["weather"][0]["id"],
            "description": current_data["weather"][0]["description"].title(),
            "icon": current_data["weather"][0]["icon"],
            "is_day": "d" in current_data["weather"][0]["icon"],
            "timestamp": current_data["dt"],
# BRACKET_SURGEON: disabled
#         },
        "forecast": [],
        "provider": "openweathermap",
# BRACKET_SURGEON: disabled
#     }

    # Add forecast data (group by day)
    if forecast_data.get("list"):
        daily_forecasts = {}
        for item in forecast_data["list"]:
            date = item["dt_txt"].split(" ")[0]  # Get date part
            if date not in daily_forecasts:
                daily_forecasts[date] = {
                    "date": date,
                    "temperatures": [],
                    "descriptions": [],
                    "precipitation": 0,
                    "wind_speeds": [],
                    "weather_codes": [],
# BRACKET_SURGEON: disabled
#                 }

            daily_forecasts[date]["temperatures"].append(item["main"]["temp"])
            daily_forecasts[date]["descriptions"].append(item["weather"][0]["description"])
            daily_forecasts[date]["precipitation"] += item.get("rain", {}).get("3h", 0) + item.get(
                "snow", {}
            ).get("3h", 0)
            daily_forecasts[date]["wind_speeds"].append(item.get("wind", {}).get("speed", 0))
            daily_forecasts[date]["weather_codes"].append(item["weather"][0]["id"])

        # Convert to forecast format
        for date, day_data in list(daily_forecasts.items())[:5]:  # Limit to 5 days
            temps = day_data["temperatures"]
            weather_data["forecast"].append(
                {
                    "date": date,
                    "temperature_max": max(temps) if temps else None,
                    "temperature_min": min(temps) if temps else None,
                    "weather_code": (
                        day_data["weather_codes"][0] if day_data["weather_codes"] else None
# BRACKET_SURGEON: disabled
#                     ),
                    "description": (
                        day_data["descriptions"][0].title()
                        if day_data["descriptions"]
                        else "Unknown"
# BRACKET_SURGEON: disabled
#                     ),
                    "precipitation_sum": day_data["precipitation"],
                    "precipitation_probability": None,  # Not available in this endpoint
                    "wind_speed_max": (
                        max(day_data["wind_speeds"]) if day_data["wind_speeds"] else None
# BRACKET_SURGEON: disabled
#                     ),
                    "sunrise": None,  # Not available in this endpoint
                    "sunset": None,  # Not available in this endpoint
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             )

    return {
        "success": True,
        "weather": weather_data,
        "quota_remaining": None,  # OpenWeatherMap doesn't provide quota in response
# BRACKET_SURGEON: disabled
#     }


def fetch_weather(
    location: str,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    max_retries: int = 1,
) -> Dict[str, Any]:
    """Fetch weather data using the active provider with automatic failover."""
    start_time = time.time()

    # Get coordinates if not provided
    if lat is None or lon is None:
        coords = _geocode_location(location)
        if not coords:
            return {
                "provider": "unknown",
                "ok": False,
                "error": f"Could not geocode location: {location}",
                "took_ms": int((time.time() - start_time) * 1000),
# BRACKET_SURGEON: disabled
#             }
        lat, lon = coords

    for attempt in range(max_retries + 1):
        try:
            # Get active provider
            active = get_active_weather_provider()
            provider_key = active["key"]

            logger.info(f"Fetching weather from {provider_key} (attempt {attempt + 1})")

            # Get credentials
            creds = _get_credentials(provider_key)
            if active.get("needs_key", False) and not creds:
                error_msg = f"No credentials found for {provider_key}"
                _report_usage(
                    provider_key,
                    False,
                    error_msg,
                    int((time.time() - start_time) * 1000),
# BRACKET_SURGEON: disabled
#                 )
                return {"provider": provider_key, "ok": False, "error": error_msg}

            # Call appropriate provider
            result = None
            if provider_key == "open - meteo":
                result = _fetch_openmeteo_weather(lat, lon, location)
            elif provider_key == "openweathermap" and "api_key" in creds:
                result = _fetch_openweathermap_weather(lat, lon, location, creds["api_key"])
            else:
                result = {
                    "success": False,
                    "error": f"No adapter implementation for {provider_key}",
# BRACKET_SURGEON: disabled
#                 }

            took_ms = int((time.time() - start_time) * 1000)

            if result["success"]:
                # Success - report and return
                _report_usage(provider_key, True, None, took_ms, result.get("quota_remaining"))
                return {
                    "provider": provider_key,
                    "ok": True,
                    "data": result["weather"],
                    "took_ms": took_ms,
# BRACKET_SURGEON: disabled
#                 }
            else:
                # Failure - report and potentially rotate
                error_msg = result.get("error", "Unknown error")
                _report_usage(provider_key, False, error_msg, took_ms)

                # Try rotation if this is not the last attempt
                if attempt < max_retries:
                    try:
                        logger.info(f"Rotating from failed provider {provider_key}")
                        rotate_resp = requests.post(
                            f"{BASE}/integrations / rotate?category = weather",
                            timeout=10,
# BRACKET_SURGEON: disabled
#                         )
                        if rotate_resp.status_code == 200:
                            rotation_data = rotate_resp.json()
                            logger.info(f"Rotated to {rotation_data.get('rotated_to', 'unknown')}")
                            continue  # Try again with new provider
                        else:
                            logger.warning(f"Failed to rotate providers: {rotate_resp.status_code}")
                    except Exception as e:
                        logger.warning(f"Error during provider rotation: {e}")

                # Return error if no more retries
                return {
                    "provider": provider_key,
                    "ok": False,
                    "error": error_msg,
                    "took_ms": took_ms,
# BRACKET_SURGEON: disabled
#                 }

        except Exception as e:
            took_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Adapter error: {str(e)}"
            logger.error(error_msg)

            # Try to report if we have a provider key
            try:
                active = get_active_weather_provider()
                _report_usage(active["key"], False, error_msg, took_ms)
            except Exception:
                pass

            return {
                "provider": "unknown",
                "ok": False,
                "error": error_msg,
                "took_ms": took_ms,
# BRACKET_SURGEON: disabled
#             }

    # Should not reach here
    return {
        "provider": "unknown",
        "ok": False,
        "error": "Max retries exceeded",
        "took_ms": int((time.time() - start_time) * 1000),
# BRACKET_SURGEON: disabled
#     }


# Convenience function for backward compatibility


def get_weather(
    location: str, lat: Optional[float] = None, lon: Optional[float] = None
) -> Optional[Dict[str, Any]]:
    """Get weather data and return just the weather object."""
    result = fetch_weather(location, lat, lon)
    if result["ok"]:
        return result["data"]
    else:
        logger.error(f"Weather fetch failed: {result['error']}")
        return None