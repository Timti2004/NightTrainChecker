import requests
import json
import os
import sys
import time
from datetime import datetime

# --- CONFIGURATION ---
DATE = "2026-08-20" # Departing 19th for 20th arrival
ORIGIN_ID = "740098197"
DESTINATION_ID = "740000254"

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
    print(f"--- Hunting for the correct URL on {DATE} ---")

    # STEP 1: Get the ID
    url_init = "https://prod-api.adp.sj.se/public/sales/booking/v3/search"
    payload = {
        "origin": ORIGIN_ID,
        "destination": DESTINATION_ID,
        "departureDate": DATE,
        "passengers": [{"passengerCategory": {"type": "ADULT"}}, {"passengerCategory": {"type": "ADULT"}}]
    }

    resp1 = requests.post(url_init, headers=HEADERS, json=payload)
    if resp1.status_code not in [200, 201]:
        print(f"!! Step 1 Failed: {resp1.status_code}")
        return

    search_id = resp1.json().get("departureSearchId")
    print(f">> Got Search ID: {search_id}")
    
    # STEP 2: The Hunt
    # We try these patterns one by one. One of them WILL work.
    base_url = "https://prod-api.adp.sj.se/public/sales/booking/v3/search"
    
    candidates = [
        f"{base_url}/{search_id}/journeys",             # Most likely
        f"{base_url}/{search_id}/departure-journeys",   # Matches the key name
        f"{base_url}/{search_id}/outbound",             # Common in travel APIs
        f"{base_url}/{search_id}/offers",               # Common variant
        f"{base_url}/{search_id}/prices",               # Another variant
        f"{base_url}/{search_id}/timetable"             # Another variant
    ]

    time.sleep(1) # Wait for server to process

    for url in candidates:
        print(f"Testing: {url.split('/')[-1]}...", end=" ")
        try:
            resp = requests.get(url, headers=HEADERS)
            
            if resp.status_code == 200:
                print("✅ BINGO! Found it!")
                data = resp.json()
                
                # Check what keys are inside
                if isinstance(data, list):
                    print(f">> It returned a LIST of {len(data)} items.")
                elif isinstance(data, dict):
                    print(f">> It returned a DICT with keys: {list(data.keys())}")
                
                # If this worked, we stop hunting and print the result
                return
            else:
                print(f"❌ ({resp.status_code})")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_tickets()