import requests
import time

class SJClient:
    """Client for interacting with the SJ Public API."""
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "ocp-apim-subscription-key": "d6625619def348d38be070027fd24ff6",
        "x-client-name": "sjse-booking-client"
    }

    def search_departures(self, origin, destination, date):
        """Initiates a search for departures on a specific date."""
        url = "https://prod-api.adp.sj.se/public/sales/booking/v3/search"
        payload = {
            "origin": origin,
            "destination": destination,
            "departureDate": date,
            "passengers": [
                {"passengerCategory": {"type": "ADULT"}}, 
                {"passengerCategory": {"type": "ADULT"}}
            ]
        }
        
        try:
            resp = requests.post(url, headers=self.HEADERS, json=payload)
            if resp.status_code != 200:
                print(f"!! Search initialization failed: {resp.status_code}")
                return None
            return resp.json().get("departureSearchId")
        except Exception as e:
            print(f"!! API Search Error: {e}")
            return None

    def fetch_results(self, search_id):
        """Fetches the detailed results for a previously initiated search."""
        url = f"https://prod-api.adp.sj.se/public/sales/booking/v3/departures/search/{search_id}"
        try:
            resp = requests.get(url, headers=self.HEADERS)
            if resp.status_code != 200:
                print(f"!! Results fetch failed: {resp.status_code}")
                return None
            return resp.json()
        except Exception as e:
            print(f"!! API Fetch Error: {e}")
            return None

    def get_offers(self, departure_id):
        """Retrieves pricing and availability offers for a specific departure."""
        url = f"https://prod-api.adp.sj.se/public/sales/booking/v3/departures/{departure_id}/offers"
        try:
            resp = requests.get(url, headers=self.HEADERS)
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception as e:
            print(f"!! API Offer Error: {e}")
            return None
