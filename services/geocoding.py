import requests
from config import NOMINATIM_URL


def reverse_geocode(lat, lon, timeout=10):
    """
    Reverse geocode coordinates to get human-readable address.
    
    Args:
        lat: Latitude
        lon: Longitude
        timeout: Request timeout in seconds
    
    Returns:
        str: Human-readable address or error message
    """
    try:
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "addressdetails": 1
        }
        headers = {
            "User-Agent": "AI-Accident-Detection/1.0"
        }
        
        response = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=timeout)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                # Try to get a comprehensive address
                address_parts = []
                
                # Get various address components
                address_data = data.get("address", {})
                
                if address_data.get("house_number"):
                    address_parts.append(address_data["house_number"])
                if address_data.get("road"):
                    address_parts.append(address_data["road"])
                if address_data.get("suburb"):
                    address_parts.append(address_data["suburb"])
                if address_data.get("city"):
                    address_parts.append(address_data["city"])
                elif address_data.get("town"):
                    address_parts.append(address_data["town"])
                elif address_data.get("village"):
                    address_parts.append(address_data["village"])
                if address_data.get("state"):
                    address_parts.append(address_data["state"])
                if address_data.get("country"):
                    address_parts.append(address_data["country"])
                
                if address_parts:
                    return ", ".join(address_parts)
                
                # Fallback to display name
                return data.get("display_name", f"Location: {lat}, {lon}")
        
        print(f"Geocoding failed with status: {response.status_code}")
        return f"Location: {lat}, {lon}"
    
    except requests.exceptions.Timeout:
        print("Geocoding timeout - using coordinates")
        return f"Location: {lat}, {lon}"
    except Exception as e:
        print(f"Geocoding error: {e}")
        return f"Location: {lat}, {lon}"


def geocode_address(address, timeout=10):
    """
    Forward geocode an address to get coordinates.
    
    Args:
        address: Address string
        timeout: Request timeout in seconds
    
    Returns:
        dict: {"lat": float, "lon": float} or None
    """
    try:
        params = {
            "q": address,
            "format": "json",
            "limit": 1
        }
        headers = {
            "User-Agent": "AI-Accident-Detection/1.0"
        }
        
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params=params,
            headers=headers,
            timeout=timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return {
                    "lat": float(data[0]["lat"]),
                    "lon": float(data[0]["lon"])
                }
        
        return None
    
    except Exception as e:
        print(f"Geocoding error: {e}")
        return None

