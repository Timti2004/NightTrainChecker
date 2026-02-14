import requests
import json
import os
import sys
import time
from datetime import datetime

# --- CONFIGURATION ---
# IMPORTANT: Departing on the 19th to arrive on the 20th morning.
DATE = "2026-08-20"
ORIGIN_ID = "740098197"       # Arlanda Flygplats
DESTINATION_ID = "740000254"  # Gällivare C

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

def send_telegram_alert(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(">> No Telegram config.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message})

def check_tickets():
    print(f"--- Checking Arlanda to Gällivare on {DATE} ---")

    url_init = "https://prod-api.adp.sj.se/public/sales/booking/v3/search"
    
    # Payload matches your cURL exactly
    payload = {
        "origin": ORIGIN_ID,
        "destination": DESTINATION_ID,
        "departureDate": DATE,
        "passengers": [
            {"passengerCategory": {"type": "ADULT"}},
            {"passengerCategory": {"type": "ADULT"}}
        ]
    }

    try:
        # STEP 1: Send the Search Request
        resp = requests.post(url_init, headers=HEADERS, json=payload)
        
        if resp.status_code != 200 and resp.status_code != 201:
            print(f"!! API Error {resp.status_code}: {resp.text[:500]}")
            return

        data = resp.json()
        
        # CHECK: Are the journeys right here?
        journeys = data.get("journeys", [])
        
        # If not in "journeys", sometimes they hide in "tripPlans" or "offers"
        if not journeys and "tripPlans" in data:
            journeys = data["tripPlans"]
            
        if not journeys:
            print(">> Request successful, but list is empty.")
            print(f">> Server returned keys: {list(data.keys())}")
            # If we see 'departureSearchId' but no journeys, THEN we know we need a step 2.
            if "departureSearchId" in data:
                 print(">> (It seems we DO need a second step, but let's see the keys first)")
            return

        print(f">> Success! Found {len(journeys)} journeys.")
        process_journeys(journeys)

    except Exception as e:
        print(f"!! Script Crash: {e}")

def process_journeys(journeys):
    found_target = False
    for journey in journeys:
        try:
            # Handle arrival time safely
            arrival_iso = journey.get('arrivalDateTime')
            if not arrival_iso and 'legs' in journey:
                arrival_iso = journey['legs'][-1]['arrivalDateTime']
            
            if not arrival_iso: continue

            arrival_time = datetime.fromisoformat(arrival_iso).strftime("%H:%M")
            
            # Look for arrival around 08:xx
            if "08" in arrival_time:
                is_bookable = journey.get('isBookable', True)
                price = "Unknown"
                try:
                    price = journey['priceQuote']['price']['amount']
                except: pass
                
                print(f"Found Train! Arrives: {arrival_time} | Bookable: {is_bookable} | Price: {price}")

                if is_bookable:
                    msg = (f"🚨 <b>TICKETS FOUND!</b>\n"
                           f"Arlanda ➔ Gällivare\n"
                           f"Date: {DATE}\n"
                           f"Arrive: {arrival_time}\n"
                           f"Price: {price} SEK\n"
                           f"👉 <a href='https://www.sj.se'>Buy Now</a>")
                    send_telegram_alert(msg)
                    found_target = True
        except:
            continue

    if not found_target:
        print(">> Target train found in schedule but NOT bookable yet.")

if __name__ == "__main__":
    check_tickets()