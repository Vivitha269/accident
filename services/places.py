import requests

def find_nearest_police(lat, lon):
    """
    Fetches the nearest police station name and location.
    Uses your direct call logic (+919342170059) for the phone number 
    to avoid Twilio short-code crashes.
    """
    query = f"""
    [out:json];
    node["amenity"="police"](around:5000,{lat},{lon});
    out body;
    """
    try:
        # Request data from Overpass API
        response = requests.post("https://overpass-api.de/api/interpreter", data=query, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("elements"):
                p = data["elements"][0]
                tags = p.get("tags", {})
                return {
                    "name": tags.get("name", "Local Police Station"),
                    "phone": "+919342170059", # Direct call for demo
                    "lat": p["lat"],
                    "lon": p["lon"]
                }
    except Exception as e:
        print(f"Police Search API Error: {e}")
    
    # Absolute fallback if API fails
    return {
        "name": "Chennai Police Control Room", 
        "phone": "+919342170059", 
        "lat": lat, 
        "lon": lon
    }

def find_top_3_hospitals(lat, lon):
    """
    Fetches top 3 hospitals near the accident location.
    Provides real names for the map markers but safe numbers for Twilio.
    """
    query = f"""
    [out:json];
    node["amenity"="hospital"](around:5000,{lat},{lon});
    out body;
    """
    hospitals = []
    try:
        response = requests.post("https://overpass-api.de/api/interpreter", data=query, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            for element in data.get("elements", []):
                tags = element.get("tags", {})
                hospitals.append({
                    "name": tags.get("name", "Nearby Hospital"),
                    # Use a verified 10-digit number for demo or default 108 string
                    "phone": "+91XXXXXXXXXX", # Replace with your test mobile number
                    "lat": element["lat"],
                    "lon": element["lon"]
                })
    except Exception as e:
        print(f"Hospital Search API Error: {e}")

    # If no hospitals found or API failed, return a default record
    if not hospitals:
        return [{
            "name": "General Hospital (Emergency)", 
            "phone": "+91XXXXXXXXXX", 
            "lat": lat, 
            "lon": lon
        }]
        
    return hospitals[:3]