"""
Routing Service - Get routes and directions using OSRM.
Optimized for faster response times with better error handling.
"""

import requests
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# OSRM API endpoints (with fallback)
OSRM_ENDPOINTS = [
    "https://router.project-osrm.org",
    "https://routing.openstreetmap.de/routed-car",
]

# Timeout for API requests
OSRM_TIMEOUT = 8  # Reduced for faster response


def _make_osrm_request(url: str, params: dict) -> Optional[dict]:
    """
    Make request to OSRM API with error handling.
    Returns JSON response or None if request fails.
    """
    try:
        response = requests.get(url, params=params, timeout=OSRM_TIMEOUT)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"OSRM API returned status {response.status_code}")
            
    except requests.exceptions.Timeout:
        logger.warning(f"OSRM API timeout for URL: {url}")
    except requests.exceptions.RequestException as e:
        logger.warning(f"OSRM API error: {e}")
    
    return None


def get_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> Optional[Dict]:
    """
    Get route between two points using OSRM.
    Returns route details or None if request fails.
    """
    url = f"{OSRM_ENDPOINTS[0]}/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}"
    params = {
        "overview": "full",
        "geometries": "geojson"
    }
    
    data = _make_osrm_request(url, params)
    
    if data and data.get("code") == "Ok":
        route = data["routes"][0]
        return {
            "distance_km": route["distance"] / 1000,
            "duration_min": route["duration"] / 60,
            "geometry": route["geometry"]
        }
    
    return None


def get_directions_text(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> Optional[str]:
    """
    Get driving directions as text for SMS messages.
    Returns a formatted string with directions or None if request fails.
    """
    url = f"{OSRM_ENDPOINTS[0]}/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}"
    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "true"
    }
    
    try:
        data = _make_osrm_request(url, params)
        
        if not data or data.get("code") != "Ok":
            return None
        
        route = data["routes"][0]
        distance_km = route["distance"] / 1000
        duration_min = route["duration"] / 60
        
        # Get turn-by-turn instructions
        directions = []
        for leg in route.get("legs", []):
            for step in leg.get("steps", []):
                maneuver = step.get("maneuver", {})
                maneuver_type = maneuver.get("type", "")
                modifier = maneuver.get("modifier", "")
                step_name = step.get("name", "")
                
                if maneuver_type:
                    instruction = f"{maneuver_type}"
                    if modifier:
                        instruction += f" {modifier}"
                    if step_name:
                        instruction += f" onto {step_name}"
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
        logger.error(f"Error getting directions: {e}")
        return None

