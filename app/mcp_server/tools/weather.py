"""
Weather tool using Open-Meteo (free, no API key required).
Two-step process: geocode the city name, then fetch current weather.
"""

import httpx

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Open-Meteo returns numeric weather codes; map the common ones to readable text.
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    95: "Thunderstorm",
}


def get_current_weather(city: str) -> dict:
    """Get the current weather for a given city name."""
    # Step 1: geocode the city name to coordinates
    geo_response = httpx.get(GEOCODING_URL, params={"name": city, "count": 1}, timeout=10.0)
    geo_response.raise_for_status()
    geo_data = geo_response.json()

    if not geo_data.get("results"):
        raise ValueError(f"Could not find a location named '{city}'.")

    location = geo_data["results"][0]
    lat, lon = location["latitude"], location["longitude"]
    resolved_name = f"{location['name']}, {location.get('country', '')}"

    # Step 2: fetch current weather for those coordinates
    weather_response = httpx.get(
        FORECAST_URL,
        params={"latitude": lat, "longitude": lon, "current_weather": "true"},
        timeout=10.0,
    )
    weather_response.raise_for_status()
    weather_data = weather_response.json()

    current = weather_data["current_weather"]
    code = current["weathercode"]

    return {
        "location": resolved_name,
        "temperature_celsius": current["temperature"],
        "windspeed_kmh": current["windspeed"],
        "condition": WEATHER_CODES.get(code, "Unknown"),
    }