import requests
import json
from config import OVERPASS_URL


def find_nearest_police(lat, lon, radius=5000):
    """
    Find nearest police station using Overpass API.
    
    Args:
        lat: Latitude
        lon: Longitude
        radius: Search radius in meters (default 5km)
    
    Returns:
        dict: Police station info with name, phone, lat, lon
    """
    # Overpass query for police
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="police"](around:{radius},{lat},{lon});
      way["amenity"="police"](around:{radius},{lat},{lon});
      relation["amenity"="police"](around:{radius},{lat},{lon});
    );
    out center;
    """
    
    try:
        response = requests.post(OVERPASS_URL, data={"data": query}, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            elements = data.get("elements", [])
            
            if elements:
                # Find the closest one
                nearest = None
                min_dist = float('inf')
                
                for element in elements:
                    if element.get("type") == "node":
                        elem_lat = element.get("lat")
                        elem_lon = element.get("lon")
                    elif element.get("type") in ["way", "relation"] and "center" in element:
                        elem_lat = element["center"].get("lat")
                        elem_lon = element["center"].get("lon")
                    else:
                        continue
                    
                    if elem_lat and elem_lon:
                        # Calculate distance (simple approximation)
                        dist = ((elem_lat - lat)**2 + (elem_lon - lon)**2)**0.5
                        if dist < min_dist:
                            min_dist = dist
                            nearest = element
                
                if nearest:
                    tags = nearest.get("tags", {})
                    return {
                        "name": tags.get("name", tags.get("official_name", "Police Station")),
                        "phone": tags.get("phone", tags.get("contact:phone", "")),
                        "lat": nearest.get("lat", nearest.get("center", {}).get("lat")),
                        "lon": nearest.get("lon", nearest.get("center", {}).get("lon"))
                    }
        
        print(f"No police stations found via Overpass API")
        
    except Exception as e:
        print(f"Overpass API error (police): {e}")
    
    # Return default police info if API fails
    return {
        "name": "Local Police",
        "phone": "+1000000000",
        "lat": lat,
        "lon": lon
    }


def find_top_3_hospitals(lat, lon, radius=10000):
    """
    Find top 3 nearest hospitals using Overpass API.
    
    Args:
        lat: Latitude
        lon: Longitude
        radius: Search radius in meters (default 10km)
    
    Returns:
        list: List of hospital info dictionaries (max 3)
    """
    # Overpass query for hospitals
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="hospital"](around:{radius},{lat},{lon});
      way["amenity"="hospital"](around:{radius},{lat},{lon});
      relation["amenity"="hospital"](around:{radius},{lat},{lon});
      node["healthcare"="hospital"](around:{radius},{lat},{lon});
      way["healthcare"="hospital"](around:{radius},{lat},{lon});
    );
    out center;
    """
    
    hospitals = []
    
    try:
        response = requests.post(OVERPASS_URL, data={"data": query}, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            elements = data.get("elements", [])
            
            # Calculate distance for each hospital
            hospital_list = []
            
            for element in elements:
                if element.get("type") == "node":
                    elem_lat = element.get("lat")
                    elem_lon = element.get("lon")
                elif element.get("type") in ["way", "relation"] and "center" in element:
                    elem_lat = element["center"].get("lat")
                    elem_lon = element["center"].get("lon")
                else:
                    continue
                
                if elem_lat and elem_lon:
                    # Calculate distance (simple approximation in degrees)
                    dist = ((elem_lat - lat)**2 + (elem_lon - lon)**2)**0.5
                    tags = element.get("tags", {})
                    
                    hospital_list.append({
                        "name": tags.get("name", tags.get("official_name", "Hospital")),
                        "phone": tags.get("phone", tags.get("contact:phone", "")),
                        "lat": elem_lat,
                        "lon": elem_lon,
                        "distance": dist
                    })
            
            # Sort by distance and take top 3
            hospital_list.sort(key=lambda x: x["distance"])
            hospitals = hospital_list[:3]
            
    except Exception as e:
        print(f"Overpass API error (hospitals): {e}")
    
    # Return default hospital if API fails
    if not hospitals:
        return [{
            "name": "City Hospital",
            "phone": "+1000000002",
            "lat": lat,
            "lon": lon
        }]
    
    return hospitals


def find_nearest_ambulance(lat, lon, radius=10000):
    """
    Find nearest ambulance service using Overpass API.
    
    Args:
        lat: Latitude
        lon: Longitude
        radius: Search radius in meters
    
    Returns:
        dict: Ambulance service info
    """
    # Overpass query for ambulance
    query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="ambulance_station"](around:{radius},{lat},{lon});
      way["amenity"="ambulance_station"](around:{radius},{lat},{lon});
      node["emergency"="ambulance"](around:{radius},{lat},{lon});
      way["emergency"="ambulance"](around:{radius},{lat},{lon});
    );
    out center;
    """
    
    try:
        response = requests.post(OVERPASS_URL, data={"data": query}, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            elements = data.get("elements", [])
            
            if elements:
                nearest = None
                min_dist = float('inf')
                
                for element in elements:
                    if element.get("type") == "node":
                        elem_lat = element.get("lat")
                        elem_lon = element.get("lon")
                    elif element.get("type") in ["way", "relation"] and "center" in element:
                        elem_lat = element["center"].get("lat")
                        elem_lon = element["center"].get("lon")
                    else:
                        continue
                    
                    if elem_lat and elem_lon:
                        dist = ((elem_lat - lat)**2 + (elem_lon - lon)**2)**0.5
                        if dist < min_dist:
                            min_dist = dist
                            nearest = element
                
                if nearest:
                    tags = nearest.get("tags", {})
                    return {
                        "name": tags.get("name", "Ambulance Service"),
                        "phone": tags.get("phone", tags.get("contact:phone", "")),
                        "lat": nearest.get("lat", nearest.get("center", {}).get("lat")),
                        "lon": nearest.get("lon", nearest.get("center", {}).get("lon"))
                    }
    
    except Exception as e:
        print(f"Overpass API error (ambulance): {e}")
    
    # Return default ambulance
    return {
        "name": "Ambulance Service",
        "phone": "+1000000001",
        "lat": lat,
        "lon": lon
    }

