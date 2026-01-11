# No API calls needed here anymore
# Replace with the two mobile numbers you will use for the demo
POLICE_MOBILE = "+919342170059"  
HOSPITAL_MOBILE = "+917338903743" 

 # REPLACE WITH YOUR SECOND MOBILE

def find_nearest_police(lat, lon):
    """Returns hardcoded police info without calling any API."""
    return {
        "name": "Local Police Station",
        "phone": POLICE_MOBILE,
        "lat": lat,
        "lon": lon
    }

def find_top_3_hospitals(lat, lon):
    """Returns hardcoded hospital info without calling any API."""
    return [{
        "name": "Emergency Hospital",
        "phone": HOSPITAL_MOBILE,
        "lat": lat,
        "lon": lon
    }]