"""Fast Async Places - Cache + Parallel Overpass"""

import asyncio
import hashlib
from functools import lru_cache
from typing import Dict, List, Optional
import httpx
from config import OVERPASS_URL, DEFAULT_HOSPITAL_NUMBER, DEFAULT_POLICE_NUMBER


async def overpass_query(query: str) -> Optional[List[Dict]]:
    """Async Overpass API query."""
    headers = {"User-Agent": "AI-Accident-Detection/1.0"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(OVERPASS_URL, data={"data": query}, headers=headers)
        if resp.status_code == 200:
            return resp.json().get("elements", [])
    return None

@lru_cache(maxsize=128)
def police_query_hash(lat: float, lon: float) -> str:
    """Cache key for police query."""
    return hashlib.md5(f"{lat:.6f},{lon:.6f}".encode()).hexdigest()

@lru_cache(maxsize=128)
def hospital_query_hash(lat: float, lon: float) -> str:
    """Cache key for hospital query."""
    return hashlib.md5(f"{lat:.6f},{lon:.6f}".encode()).hexdigest()

async def find_nearest_police(lat: float, lon: float) -> Dict:
    """Find nearest police station async."""
    query = f"""
    [out:json][timeout:10];
    (
      node["amenity"="police"](around:5000,{lat},{lon});
      way["amenity"="police"](around:5000,{lat},{lon});
      relation["amenity"="police"](around:5000,{lat},{lon});
    );
    out center;
    """
    
    elements = await overpass_query(query)
    if elements:
        # Find closest (sort by distance)
        def distance(e):
            return ((e.get('lat', lat) - lat)**2 + (e.get('lon', lon)**2))**0.5
        
        closest = min(elements, key=distance)
        return {
            "name": closest.get('tags', {}).get('name', 'Police Station'),
            "phone": closest.get('tags', {}).get('phone', DEFAULT_POLICE_NUMBER),
            "lat": closest.get('lat', lat),
            "lon": closest.get('lon', lon)
        }
    return {
        "name": "Local Police",
        "phone": DEFAULT_POLICE_NUMBER,
        "lat": lat,
        "lon": lon
    }

async def find_top_3_hospitals(lat: float, lon: float) -> List[Dict]:
    """Find top 3 nearest hospitals async."""
    query = f"""
    [out:json][timeout:10];
    (
      node["amenity"~"hospital|clinic"](around:10000,{lat},{lon});
      way["amenity"~"hospital|clinic"](around:10000,{lat},{lon});
      relation["amenity"~"hospital|clinic"](around:10000,{lat},{lon});
    );
    out center;
    """
    
    elements = await overpass_query(query)
    if elements:
        def distance(e):
            return ((e.get('lat', lat) - lat)**2 + (e.get('lon', lon)**2))**0.5
        
        sorted_elements = sorted(elements, key=distance)[:3]
        hospitals = []
        for e in sorted_elements:
            hospitals.append({
                "name": e.get('tags', {}).get('name', 'Hospital'),
                "phone": e.get('tags', {}).get('phone', DEFAULT_HOSPITAL_NUMBER),
                "lat": e.get('lat', lat),
                "lon": e.get('lon', lon)
            })
        return hospitals
    return [{
        "name": "Emergency Hospital",
        "phone": DEFAULT_HOSPITAL_NUMBER,
        "lat": lat,
        "lon": lon
    }] * 3

async def find_police_and_hospitals(lat: float, lon: float):
    """Parallel query."""
    police_task = find_nearest_police(lat, lon)
    hospitals_task = find_top_3_hospitals(lat, lon)
    return await asyncio.gather(police_task, hospitals_task)
