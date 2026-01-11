import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, field_validator

from services.geocoding import reverse_geocode
from services.routing import get_route
from services.places import find_top_3_hospitals

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

templates = Jinja2Templates(directory="templates")


class LocationQuery(BaseModel):
    """Pydantic model for location queries with validation."""
    lat: float
    lon: float

    @field_validator('lat')
    @classmethod
    def validate_lat(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @field_validator('lon')
    @classmethod
    def validate_lon(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v


@app.get("/")
def home():
    return {"status": "Accident Detection API running"}


@app.get("/accident")
def accident(query: LocationQuery):
    """Get accident location details, nearest hospital, and route."""
    try:
        address = reverse_geocode(query.lat, query.lon)
        hospitals = find_top_3_hospitals(query.lat, query.lon)
        hospital = hospitals[0]
        route = get_route(query.lat, query.lon, hospital["lat"], hospital["lon"])

        return {
            "accident_location": address,
            "nearest_hospital": hospital,
            "alternative_hospitals": hospitals[1:],
            "route": route
        }
    except Exception as e:
        logger.error(f"Error in accident endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to process accident data")


@app.get("/map", response_class=HTMLResponse)
def show_map(request: Request, lat: float, lon: float, accident_id: str = None, name: str = "Unknown", status: str = "pending"):
    """Show map with accident location."""
    # Validate coordinates
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise HTTPException(status_code=400, detail="Invalid coordinates")

    return templates.TemplateResponse(
        "map.html",
        {
            "request": request,
            "lat": lat,
            "lon": lon,
            "accident_id": accident_id or "",
            "name": name,
            "status": status
        }
    )
