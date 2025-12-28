import requests

# Base URL of the API (assuming running on localhost:8000)
BASE_URL = "http://127.0.0.1:8000"

# Sample data for testing
user_id = "test_user_123"
device_token = "sample_device_token_abc"
contacts = ["+1234567890", "+0987654321"]
accident_data = {
    "userId": user_id,
    "name": "John Doe",
    "lat": 40.7128,  # New York coordinates for testing
    "lon": -74.0060
}

def test_register_device():
    url = f"{BASE_URL}/register_device"
    params = {"userId": user_id, "token": device_token}
    response = requests.post(url, params=params)
    print("Register Device:", response.status_code, response.json())

def test_add_contacts():
    url = f"{BASE_URL}/contacts"
    params = {"userId": user_id}
    json_data = {"contacts": contacts}
    response = requests.post(url, params=params, json=json_data)
    print("Add Contacts:", response.status_code, response.json())

def test_accident_report():
    url = f"{BASE_URL}/accident"
    params = accident_data
    response = requests.post(url, params=params)
    print("Accident Report:", response.status_code, response.json())

def test_map():
    url = f"{BASE_URL}/map?lat={accident_data['lat']}&lon={accident_data['lon']}"
    response = requests.get(url)
    print("Map Response:", response.status_code)
    if response.status_code == 200:
        print("Map HTML length:", len(response.text))

if __name__ == "__main__":
    print("Testing Accident API...")
    test_register_device()
    test_add_contacts()
    test_accident_report()
    test_map()
    print("Testing complete.")