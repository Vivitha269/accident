# No API calls needed here anymore
# Replace with the mobile numbers you will use for the demo
POLICE_MOBILE = "+919342170059"
HOSPITAL_MOBILE_1 = "+917338903743"
HOSPITAL_MOBILE_2 = "+919999999999"
HOSPITAL_MOBILE_3 = "+918888888888"


def find_nearest_police(lat, lon):
    """Returns hardcoded police info without calling any API."""
    return {
        "name": "Local Police Station",
        "phone": POLICE_MOBILE,
        "lat": lat,
        "lon": lon
    }


def find_top_3_hospitals(lat, lon):
    """Returns 3 hardcoded hospital info without calling any API."""
    return [
        {
            "name": "Emergency Hospital - Primary",
            "phone": HOSPITAL_MOBILE_1,
            "lat": lat,
            "lon": lon
        },
        {
            "name": "City General Hospital",
            "phone": HOSPITAL_MOBILE_2,
            "lat": lat + 0.01,  # Slightly offset coordinates
            "lon": lon + 0.01
        },
        {
            "name": " Trauma Center",
            "phone": HOSPITAL_MOBILE_3,
            "lat": lat - 0.01,
            "lon": lon - 0.01
        }
    ]
