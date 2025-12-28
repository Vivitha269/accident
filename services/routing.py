import requests

def get_route(start_lat, start_lon, end_lat, end_lon):
    url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}"
    params = {
        "overview": "full",
        "geometries": "geojson"
    }

    response = requests.get(url, params=params)
    data = response.json()

    if data["code"] != "Ok":
        return "Route not found"

    route = data["routes"][0]
    return {
        "distance_km": route["distance"] / 1000,
        "duration_min": route["duration"] / 60,
        "geometry": route["geometry"]
    }
