import requests
import json
import os
import sys
import time
from datetime import datetime

# --- CONFIGURATION ---
DATE = "2026-03-20"  # Testing date from your screenshot
ORIGIN_ID = "740000556" # Arlanda Central
DESTINATION_ID = "740000254" # Gällivare C

# Secrets
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "ocp-apim-subscription-key": "d6625619def348d38be070027fd24ff6",
    "x-client-name": "sjse-booking-client"
}

def check_tickets():
    print(f"--- Checking Night Train: {DATE} (Arlanda -> Gällivare) ---")

    url_search = "https://prod-api.adp.sj.se/public/sales/booking/v3/search"
    payload = {
        "origin": ORIGIN_ID,
        "destination": DESTINATION_ID,
        "departureDate": DATE,
        "passengers": [{"passengerCategory": {"type": "ADULT"}}, {"passengerCategory": {"type": "ADULT"}}]
    }

    try:
        resp = requests.post(url_search, headers=HEADERS, json=payload)
        data = resp.json()

        # --- DEBUG STEP ---
        # This will print everything SJ sends. We can use this to see 
        # if the train is hiding under a different key.
        print("RAW RESPONSE KEYS:", data.keys())
        
        journeys = data.get("journeys", [])

        if not journeys:
            print(">> journeys list is empty. Checking alternative keys...")
            # Some search results are wrapped in a different object structure
            if "outboundJourneys" in data:
                journeys = data["outboundJourneys"]
            elif "tripPlans" in data:
                journeys = data["tripPlans"]

        if not journeys:
            print(">> Still no trains found. Printing raw data for inspection:")
            print(json.dumps(data, indent=2)) # This will show everything in the logs
            return

        print(f">> Success! Found {len(journeys)} trains.")
        for journey in journeys:
            # We'll print every arrival time found to find the 08:08
            arrival_iso = journey.get("arrivalDateTime")
            if not arrival_iso and "legs" in journey:
                arrival_iso = journey["legs"][-1]["arrivalDateTime"]
            
            if arrival_iso:
                arrival_time = datetime.fromisoformat(arrival_iso).strftime("%H:%M")
                print(f"   - Scanned train arriving at {arrival_time}")

                if "07:30" < arrival_time < "09:30":
                    print(f">> MATCH FOUND! ID: {journey.get('id')}")

    except Exception as e:
        print(f"!! Script Crash: {e}")

if __name__ == "__main__":
    check_tickets()