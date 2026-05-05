import requests

url = "http://localhost:8000/api/predict/location-risk"
# Testing with Wayanad coordinates
data = {
    "lat": 11.6854,
    "lng": 76.1320
}

try:
    response = requests.post(url, json=data)
    print("API Response:", response.json())
except Exception as e:
    print("Error:", e)
