import requests
import json
import os
import sys
from datetime import datetime

# --- CONFIGURATION ---
DATE = "2026-08-20"
# Using the exact UIC codes from your intercepted traffic
ORIGIN_ID = "740098197"       # Arlanda Flygplats
DESTINATION_ID = "740000254"  # Gällivare C/Resecentrum

# Secrets
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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

def check_tickets():
    print(f"--- Checking Arlanda ({ORIGIN_ID}) to Gällivare ({DESTINATION_ID}) on {DATE} ---")

    # 1. NEW ENDPOINT & PAYLOAD
    # We use the structure you found: UIC codes and 'passengers' array
    url = "https://www.sj.se/api/sales/travel-searches"
    
    payload = {
        "journeyDate": {
            "date": DATE,
            "time": "00:00"
        },
        "origin": {
            "uicStationCode": ORIGIN_ID,
            "name": "Arlanda Flygplats"
        },
        "destination": {
            "uicStationCode": DESTINATION_ID,
            "name": "Gällivare C"
        },
        "passengers": [
            {
                "passengerCategory": {
                    "type": "ADULT",
                    "age": 30
                }
            }
        ]
    }

    try:
        response = requests.post(url, headers=HEADERS, json=payload)
        
        if response.status_code != 200 and response.status_code != 201:
            print(f"!! API Error {response.status_code}")
            print(response.text[:500])
            return

        data = response.json()

        # 2. HANDLE RESULTS
        # Sometimes SJ returns a 'departureSearchId' and we have to fetch results separately.
        # Check if we have journeys immediately or need a second step.
        
        journeys = []
        
        if "journeys" in data:
            journeys = data["journeys"]
        elif "departureSearchId" in data:
            # If they give us an ID, we might need to query it. 
            # (Usually, the POST returns journeys too, but let's be safe)
            search_id = data["departureSearchId"]
            print(f">> Search initiated (ID: {search_id}). checking for journeys in response...")
            # Some versions of the API return journeys inside this same object, 
            # let's look for 'offers' or 'schedule'.
            # If strictly empty, we might need a GET request here. 
            # For now, let's assume standard behavior.
        
        if not journeys and "tripPlans" in data:
             journeys = data["tripPlans"]

        if not journeys:
            print(">> No journeys found in the response object.")
            # Debug: Print keys to see where the data is hiding
            print(f"Available keys: {data.keys()}")
            return

        found_target = False
        for journey in journeys:
            # Adjust parsing based on actual response structure
            # The new API might use 'arrivalDateTime' or nested segments
            
            # Safe extraction of arrival time
            try:
                arrival_iso = journey.get('arrivalDateTime')
                if not arrival_iso:
                    # Fallback for complex itineraries
                    arrival_iso = journey['legs'][-1]['arrivalDateTime']
                
                arrival_time = datetime.fromisoformat(arrival_iso).strftime("%H:%M")
                
                # Check for morning arrival (approx 08:24)
                if "08" in arrival_time:
                    is_bookable = journey.get('isBookable', True) # Default to true if key missing
                    
                    # Try to find price
                    price = "Unknown"
                    try:
                        price = journey['priceQuote']['price']['amount']
                    except:
                        pass

                    print(f"Found Train! Arrives: {arrival_time}. Bookable: {is_bookable}")

                    if is_bookable:
                        msg = (f"🚨 <b>TICKETS FOUND!</b>\n"
                               f"Arlanda ➔ Gällivare\n"
                               f"Date: {DATE}\n"
                               f"Arrival: {arrival_time}\n"
                               f"Price: {price}\n"
                               f"👉 <a href='https://www.sj.se'>Buy Now</a>")
                        send_telegram_alert(msg)
                        found_target = True
            except Exception as e:
                print(f"Error parsing a journey: {e}")
                continue
        
        if not found_target:
            print(">> Targeted train not found or not bookable yet.")

    except Exception as e:
        print(f"!! Script Crash: {e}")

if __name__ == "__main__":
    check_tickets()