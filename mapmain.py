from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from services.geocoding import reverse_geocode
from services.routing import get_route
from services.places import find_nearest_hospital

app = FastAPI()

templates = Jinja2Templates(directory="templates")


@app.get("/")
def home():
    return {"status": "Accident Detection API running"}


@app.get("/accident")
def accident(lat: float, lon: float):
    address = reverse_geocode(lat, lon)
    hospital = find_nearest_hospital(lat, lon)
    route = get_route(lat, lon, hospital["lat"], hospital["lon"])

    return {
        "accident_location": address,
        "nearest_hospital": hospital,
        "route": route
    }


@app.get("/map", response_class=HTMLResponse)
def show_map(request: Request, lat: float, lon: float):
    return templates.TemplateResponse(
        "map.html",
        {"request": request, "lat": lat, "lon": lon}
    )
