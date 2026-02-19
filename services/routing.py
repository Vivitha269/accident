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


def get_directions_text(start_lat, start_lon, end_lat, end_lon):
    """
    Get driving directions as text for SMS messages.
    Returns a formatted string with directions.
    """
    url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}"
    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "true"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data["code"] != "Ok":
            return None

        route = data["routes"][0]
        distance_km = route["distance"] / 1000
        duration_min = route["duration"] / 60

        # Get turn-by-turn instructions
        directions = []
        for leg in route.get("legs", []):
            for step in leg.get("steps", []):
                instruction = step.get("maneuver", {}).get("instruction", "")
                if not instruction:
                    # Fallback: use maneuver type
                    maneuver_type = step.get("maneuver", {}).get("type", "")
                    modifier = step.get("maneuver", {}).get("modifier", "")
                    if maneuver_type:
                        instruction = f"{maneuver_type} {modifier}".strip() if modifier else maneuver_type
                        if step.get("name"):
                            instruction += f" onto {step.get('name')}"
                if instruction:
                    directions.append(instruction)

        # Build formatted directions text
        directions_text = f"📍 Distance: {distance_km:.1f} km | Time: {duration_min:.0f} min\n"
        
        if directions:
            directions_text += "🧭 Directions:\n"
            for i, direction in enumerate(directions[:5], 1):  # Limit to first 5 steps for SMS
                directions_text += f"{i}. {direction}\n"
        else:
            directions_text += f"🗺️ Google Maps: https://www.google.com/maps/dir/{start_lat},{start_lon}/{end_lat},{end_lon}"

        return directions_text.strip()

    except Exception as e:
        print(f"Error getting directions: {e}")
        return None
