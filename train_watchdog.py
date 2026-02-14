import requests
import json
import os
import sys
from datetime import datetime

# --- CONFIGURATION ---
DATE = "2026-08-20"  # Travel Date
ORIGIN_NAME = "Stockholm Arlanda" 
DESTINATION_NAME = "Gällivare C"

# TARGET ARRIVAL TIME (HH:MM)
TARGET_ARRIVAL = "08:24"
# Allow a buffer in case schedule changes slightly (+/- 30 mins)
# If the train arrives between 07:54 and 08:54, it will trigger.

# Secrets (Set these in GitHub Secrets)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def send_telegram_alert(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(">> No Telegram config. Message:")
        print(message)
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"!! Telegram Fail: {e}")

def get_location_id(search_string):
    url = "https://www.sj.se/api/typeahead/places"
    params = {"query": search_string}
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        return response.json()[0]['id']
    except Exception:
        sys.exit(f"Could not find station ID for {search_string}")

def parse_time(iso_string):
    # Extracts HH:MM from "2026-08-20T08:24:00"
    return datetime.fromisoformat(iso_string).strftime("%H:%M")

def check_tickets():
    print(f"--- Checking {ORIGIN_NAME} to {DESTINATION_NAME} on {DATE} ---")
    
    origin_id = get_location_id(ORIGIN_NAME)
    dest_id = get_location_id(DESTINATION_NAME)

    url = "https://www.sj.se/api/sales/travel-searches"
    payload = {
        "travelers": [{"type": "ADULT"}],
        "journeyDate": {"date": DATE, "time": "00:00"},
        "origin": {"id": origin_id, "type": "STATION"},
        "destination": {"id": dest_id, "type": "STATION"}
    }

    try:
        response = requests.post(url, headers=HEADERS, json=payload)
        data = response.json()
        
        found_target = False

        if "journeys" not in data:
            print("No journeys found in API response (Tickets likely not released).")
            return

        for journey in data['journeys']:
            # The arrival time of the whole journey is usually the last leg's arrival
            arrival_iso = journey['arrivalDateTime']
            arrival_time = parse_time(arrival_iso)
            
            # Simple check: Does it arrive around 08:24?
            # We check if it matches exactly OR is very close (Vy 94 usually arrives 08:00-09:00)
            if "08" in arrival_time: 
                is_bookable = journey['isBookable']
                price_info = journey.get('priceQuote', {}).get('price', {})
                price = price_info.get('amount', "N/A")
                currency = price_info.get('currency', "SEK")

                print(f"Found Train! Arrives: {arrival_time}. Bookable: {is_bookable}")

                if is_bookable:
                    msg = (f"🚨 <b>TICKETS RELEASED!</b>\n"
                           f"Arlanda ➔ Gällivare\n"
                           f"Date: {DATE}\n"
                           f"Arrival: {arrival_time}\n"
                           f"Price: {price} {currency}\n"
                           f"👉 <a href='https://www.sj.se'>Buy Now on SJ.se</a>")
                    send_telegram_alert(msg)
                    found_target = True
        
        if not found_target:
            print(">> Target train found in schedule but NOT bookable yet.")

    except Exception as e:
        print(f"Error: {e}")
        # Optional: Send alert on script failure so you know if it breaks
        # send_telegram_alert(f"Script Error: {e}")

if __name__ == "__main__":
    check_tickets()