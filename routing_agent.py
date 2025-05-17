from math import radians, cos, sin, asin, sqrt

# Hardcoded airport coordinates for demo
AIRPORT_COORDS = {
    "San Francisco": (37.6213, -122.3790),
    "Las Vegas": (36.0840, -115.1537),
    "Los Angeles": (33.9416, -118.4085),
    "New York": (40.7128, -74.0060),
    "Chicago": (41.8781, -87.6298),
}


# Simple Haversine distance calculator
def haversine_distance_km(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of earth in kilometers
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c

def enrich_with_routing_info(trip, aircraft_list):
    origin = trip.get("origin")
    destination = trip.get("destination")
    if origin not in AIRPORT_COORDS or destination not in AIRPORT_COORDS:
        return aircraft_list  # Skip if coordinates are missing

    lat1, lon1 = AIRPORT_COORDS[origin]
    lat2, lon2 = AIRPORT_COORDS[destination]
    distance_km = haversine_distance_km(lat1, lon1, lat2, lon2)
    average_speed_kmph = 800
    estimated_hours = distance_km / average_speed_kmph

    enriched = []
    for ac in aircraft_list:
        cost_per_hour = ac.get("cost_per_hour", 2500)
        ac["estimated_flight_time_hr"] = round(estimated_hours, 2)
        ac["estimated_cost"] = round(cost_per_hour * estimated_hours, 2)
        enriched.append(ac)
    return enriched

