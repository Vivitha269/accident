# No API calls needed here anymore
# Replace with the two mobile numbers you will use for the demo
POLICE_MOBILE = "+919342170059"  
HOSPITAL_MOBILE = "+917338903743" 

def find_nearest_police(lat, lon):
    """Returns a hardcoded police contact for the demo."""
    return {
        "name": "Chennai Local Police Station",
        "phone": POLICE_MOBILE,
        "lat": lat,
        "lon": lon
    }

def find_top_3_hospitals(lat, lon):
    """Returns a hardcoded hospital contact for the demo."""
    return [{
        "name": "Emergency Care Hospital",
        "phone": HOSPITAL_MOBILE,
        "lat": lat,
        "lon": lon
    }]