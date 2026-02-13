import requests
import json

# Overpass API endpoint for OpenStreetMap data
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Fallback phone numbers (in case API fails)
POLICE_MOBILE = "+919342170059"
HOSPITAL_MOBILE_1 = "+917338903743"
HOSPITAL_MOBILE_2 = "+919999999999"
HOSPITAL_MOBILE_3 = "+918888888888"


def find_nearest_police(lat, lon, radius=10000):
    """
    Find the nearest police station using Overpass API.
    """
    # Overpass query to find police stations
    overpass_query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="police"](around:{radius},{lat},{lon});
      way["amenity"="police"](around:{radius},{lat},{lon});
    );
    out center;
    """
    
    try:
        response = requests.get(
            OVERPASS_URL,
            params={"data": overpass_query},
            headers={"User-Agent": "AccidentAlertApp/1.0"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            elements = data.get("elements", [])
            
            if elements:
                element = elements[0]
                
                # Extract coordinates
                if element.get("type") == "node":
                    pl_lat = element.get("lat")
                    pl_lon = element.get("lon")
                else:
                    center = element.get("center", {})
                    pl_lat = center.get("lat")
                    pl_lon = center.get("lon")
                
                police_name = element.get("tags", {}).get("name", "Police Station")
                police_phone = element.get("tags", {}).get("phone", POLICE_MOBILE)
                
                print(f"Found police station: {police_name} at ({pl_lat}, {pl_lon})")
                
                return {
                    "name": police_name,
                    "phone": police_phone,
                    "lat": pl_lat,
                    "lon": pl_lon,
                    "address": f"{police_name}, Location: ({pl_lat:.4f}, {pl_lon:.4f})"
                }
        
        print("No police station found via Overpass API, using fallback")
        
    except Exception as e:
        print(f"Overpass API error for police: {e}")
    
    # Fallback to hardcoded values
    return {
        "name": "Local Police Station",
        "phone": POLICE_MOBILE,
        "lat": lat,
        "lon": lon,
        "address": "Local Police Station (fallback)"
    }


def find_top_3_hospitals(lat, lon, radius=15000):
    """
    Find top 3 nearest hospitals using Overpass API.
    """
    overpass_query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="hospital"](around:{radius},{lat},{lon});
      node["healthcare"="hospital"](around:{radius},{lat},{lon});
      way["amenity"="hospital"](around:{radius},{lat},{lon});
      way["healthcare"="hospital"](around:{radius},{lat},{lon});
    );
    out center;
    """
    
    hospitals = []
    
    try:
        response = requests.get(
            OVERPASS_URL,
            params={"data": overpass_query},
            headers={"User-Agent": "AccidentAlertApp/1.0"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            elements = data.get("elements", [])
            
            if elements:
                for i, element in enumerate(elements[:3]):
                    if element.get("type") == "node":
                        h_lat = element.get("lat")
                        h_lon = element.get("lon")
                    else:
                        center = element.get("center", {})
                        h_lat = center.get("lat")
                        h_lon = center.get("lon")
                    
                    hospital_name = element.get("tags", {}).get("name", f"Hospital {i+1}")
                    hospital_phone = element.get("tags", {}).get("phone", 
                                           [HOSPITAL_MOBILE_1, HOSPITAL_MOBILE_2, HOSPITAL_MOBILE_3][i])
                    
                    print(f"Found hospital: {hospital_name} at ({h_lat}, {h_lon})")
                    
                    hospitals.append({
                        "name": hospital_name,
                        "phone": hospital_phone,
                        "lat": h_lat,
                        "lon": h_lon,
                        "address": f"{hospital_name}, Location: ({h_lat:.4f}, {h_lon:.4f})"
                    })
        
    except Exception as e:
        print(f"Overpass API error for hospitals: {e}")
    
    # If we didn't find enough hospitals, add fallbacks
    if len(hospitals) < 3:
        fallback_hospitals = [
            {"name": "Emergency Hospital - Primary", "phone": HOSPITAL_MOBILE_1, "lat": lat, "lon": lon},
            {"name": "City General Hospital", "phone": HOSPITAL_MOBILE_2, "lat": lat + 0.01, "lon": lon + 0.01},
            {"name": "Trauma Center", "phone": HOSPITAL_MOBILE_3, "lat": lat - 0.01, "lon": lon - 0.01}
        ]
        
        for fh in fallback_hospitals:
            if len(hospitals) >= 3:
                break
            is_duplicate = False
            for h in hospitals:
                if h["lat"] == fh["lat"] and h["lon"] == fh["lon"]:
                    is_duplicate = True
                    break
            if not is_duplicate:
                fh["address"] = f"{fh['name']} (fallback)"
                hospitals.append(fh)
    
    return hospitals[:3]
