import requests
import json
import os
import sys

# --- CONFIGURATION ---
# Change these to your specific travel details
DATE = "2026-03-15"  # Format: YYYY-MM-DD
ORIGIN_NAME = "Stockholm Arlanda" # Arlanda C
DESTINATION_NAME = "Gällivare C"

# Telegram Secrets (Set these in GitHub Secrets later)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# --- HEADERS ---
# We mimic a real browser to avoid being blocked
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def send_telegram_alert(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(">> No Telegram config found. Printing to console instead:")
        print(message)
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload)
        print(">> Telegram notification sent!")
    except Exception as e:
        print(f"!! Failed to send Telegram: {e}")

def get_location_id(search_string):
    """
    SJ uses internal IDs (like 'M' for Malmö, 'Cst' for Stockholm C).
    We need to fetch the ID for Arlanda and Gällivare first.
    """
    url = "https://www.sj.se/api/typeahead/places"
    params = {"query": search_string}
    
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        data = response.json()
        # Return the first matching ID
        return data[0]['id']
    except Exception as e:
        print(f"!! Error fetching ID for {search_string}: {e}")
        sys.exit(1)

def check_tickets():
    print(f"Checking tickets for {DATE}...")
    
    # 1. Resolve Station IDs
    origin_id = get_location_id(ORIGIN_NAME)
    dest_id = get_location_id(DESTINATION_NAME)
    print(f"Resolved: {ORIGIN_NAME} -> {origin_id}, {DESTINATION_NAME} -> {dest_id}")

    # 2. Build the API Query
    # Note: The endpoint and payload structure below mimics SJ's internal API.
    # This might change if they update their site, requiring a quick patch.
    url = "https://www.sj.se/api/sales/travel-searches"
    
    payload = {
        "travelers": [{"type": "ADULT"}], # 1 Adult
        "journeyDate": {
            "date": DATE,
            "time": "00:00"
        },
        "origin": {"id": origin_id, "type": "STATION"},
        "destination": {"id": dest_id, "type": "STATION"}
    }

    try:
        response = requests.post(url, headers=HEADERS, json=payload)
        
        if response.status_code != 200:
            print(f"!! API Error: {response.status_code}")
            return

        data = response.json()
        
        # 3. Parse Results
        found_available = False
        
        # Iterate through available journeys
        for journey in data.get('journeys', []):
            # Check if it is a night train (usually takes >10 hours or marked overnight)
            is_night_train = False
            for leg in journey['legs']:
                if leg['type'] == 'TRAIN' and (leg['trainNumber'] == '94' or leg['trainNumber'] == '93'):
                    is_night_train = True
            
            # Check availability status
            if is_night_train and journey.get('isBookable', False):
                price = journey['priceQuote']['price']['amount']
                currency = journey['priceQuote']['price']['currency']
                
                msg = (f"🚂 ALERT! Night Train tickets available on {DATE}!\n"
                       f"Route: {ORIGIN_NAME} -> {DESTINATION_NAME}\n"
                       f"Price: {price} {currency}\n"
                       f"Link: https://www.sj.se")
                
                send_telegram_alert(msg)
                found_available = True
                break # Stop after finding the first valid one
        
        if not found_available:
            print(">> Night train still not available/sold out.")

    except Exception as e:
        print(f"!! Script failed: {e}")

if __name__ == "__main__":
    check_tickets()