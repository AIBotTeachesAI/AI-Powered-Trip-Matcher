import requests

NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "ai-trip-matcher/1.0"

CITY_COORDS = {
    "San Francisco": (37.7749, -122.4194),
    "Las Vegas": (36.1699, -115.1398),
    "Los Angeles": (34.0522, -118.2437),
    "New York": (40.7128, -74.0060),
    "Chicago": (41.8781, -87.6298),
}


def get_nws_forecast(lat, lon):
    headers = {"User-Agent": USER_AGENT}
    try:
        r = requests.get(f"{NWS_API_BASE}/points/{lat},{lon}", headers=headers)
        r.raise_for_status()
        forecast_url = r.json()["properties"]["forecast"]

        r2 = requests.get(forecast_url, headers=headers)
        r2.raise_for_status()
        period = r2.json()["properties"]["periods"][0]

        return {
            "summary": period["shortForecast"],
            "temperature": f"{period['temperature']} {period['temperatureUnit']}",
            "wind": f"{period['windSpeed']} {period['windDirection']}",
        }
    except Exception as e:
        return {"error": str(e)}

def get_weather_for_city(city_name):
    if city_name not in CITY_COORDS:
        return {"error": f"No coordinates for city: {city_name}"}
    lat, lon = CITY_COORDS[city_name]
    return get_nws_forecast(lat, lon)

def parse_wind_speed(wind_str):
    try:
        return int(wind_str.split()[0])
    except:
        return 0

def check_weather_for_trip(trip):
    origin = trip.get("origin")
    destination = trip.get("destination")

    origin_data = get_weather_for_city(origin)
    dest_data = get_weather_for_city(destination)

    origin_wind = parse_wind_speed(origin_data.get("wind", "0 mph"))
    dest_wind = parse_wind_speed(dest_data.get("wind", "0 mph"))

    return {
        "origin_weather": origin_data,
        "destination_weather": dest_data,
        "safe_to_fly": origin_wind < 45 and dest_wind < 45
    }
