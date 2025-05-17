import json

def load_aircraft_data():
    with open("data/aircraft.json", "r") as f:
        return json.load(f)


def match_aircrafts(trip, aircrafts):
    matches = []
    for ac in aircrafts:
        if (
            ac["seats"] >= trip["passenger_count"] and
            ac["range_km"] >= 700 and
            ac["location"].lower() == trip["origin"].lower()
        ):
            matches.append(ac)
    return matches

