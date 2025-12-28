import requests

def reverse_geocode(lat, lon):
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json"
    }
    headers = {
        "User-Agent": "Accident-App"
    }

    response = requests.get(url, params=params, headers=headers)
    data = response.json()

    return data.get("display_name", "Address not found")
