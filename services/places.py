import requests

def find_nearest_police(lat, lon):
    """Fetches the nearest police station name and phone number."""
    # Searching for police within 5km and requesting full tags for phone info
    query = f"""
    [out:json];
    node["amenity"="police"](around:5000,{lat},{lon});
    out body;
    """
    response = requests.post("https://overpass-api.de/api/interpreter", data=query).json()
    
    if response.get("elements"):
        p = response["elements"][0]
        tags = p.get("tags", {})
        return {
            "name": tags.get("name", "Local Police Station"),
            # Tries to get phone tag; falls back to 100 for Chennai
            "phone": tags.get("phone") or tags.get("contact:phone") or "+919342170059", 
            "lat": p["lat"],
            "lon": p["lon"]
        }
    return {"name": "Chennai Police Control Room", "phone": "919342170059", "lat": lat, "lon": lon}

def find_top_3_hospitals(lat, lon):
    query = f"""
    [out:json];
    node["amenity"="hospital"](around:5000,{lat},{lon});
    out body;
    """
    try:
        response = requests.post("https://overpass-api.de/api/interpreter", data=query, timeout=10)
        # Check if the response is actually JSON
        if response.status_code == 200:
            data = response.json()
        else:
            return [] # Return empty list if server error
    except Exception as e:
        print(f"Overpass Error: {e}")
        return [] # Return empty list if request fails
    
    hospitals = []
    for element in data.get("elements", []):
        tags = element.get("tags", {})
        hospitals.append({
            "name": tags.get("name", "Nearby Hospital"),
            "phone": tags.get("phone") or tags.get("contact:phone") or "108",
            "lat": element["lat"],
            "lon": element["lon"]
        })
    return hospitals[:3]