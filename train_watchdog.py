import requests
import json
import os
import sys
import time
from datetime import datetime

# --- CONFIGURATION ---
# 1. TEST DATE: March 20 (Matches your screenshot where tickets exist)
DATE = "2026-08-20"  
# Once confirmed working, change this back to "2026-08-20"

# 2. STATIONS: Arlanda Central -> Gällivare C
ORIGIN_ID = "740000556" 
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

def send_telegram_alert(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"TELEGRAM ALERT: {message}")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"})

def check_tickets():
    print(f"--- Checking Night Train: {DATE} ---")

    # STEP 1: INITIATE SEARCH
    url_init = "https://prod-api.adp.sj.se/public/sales/booking/v3/search"
    payload = {
        "origin": ORIGIN_ID,
        "destination": DESTINATION_ID,
        "departureDate": DATE,
        "passengers": [{"passengerCategory": {"type": "ADULT"}}, {"passengerCategory": {"type": "ADULT"}}]
    }

    try:
        resp1 = requests.post(url_init, headers=HEADERS, json=payload)
        if resp1.status_code != 200 and resp1.status_code != 201:
            print(f"!! Step 1 Error: {resp1.text}")
            return

        search_id = resp1.json().get("departureSearchId")
        if not search_id:
            print("!! Step 1 failed. No search ID.")
            return

        print(f">> Search Session Created: {search_id}")
        time.sleep(1) 

        # STEP 2: FETCH RESULTS (The Fixed URL)
        # We now use the URL pattern found in your logs
        url_results = f"https://prod-api.adp.sj.se/public/sales/booking/v3/departures/search/{search_id}"
        
        resp2 = requests.get(url_results, headers=HEADERS)
        if resp2.status_code != 200:
            print(f"!! Step 2 Error ({resp2.status_code}): {resp2.text[:200]}")
            return

        data2 = resp2.json()
        
        # PARSING: The structure from your uploaded JSON file
        # Root -> travels -> [0] -> departures
        travels = data2.get("travels", [])
        if not travels:
            print(">> Response valid but 'travels' list is empty.")
            return

        departures = travels[0].get("departures", [])
        print(f">> SUCCESS! Scanned {len(departures)} departures.")
        
        found_target = False
        for dep in departures:
            journey_id = dep.get("departureId")
            arrival_iso = dep.get("arrivalDateTime")
            
            if arrival_iso:
                arrival_time = datetime.fromisoformat(arrival_iso).strftime("%H:%M")
                print(f"   - Train arrives at {arrival_time}")

                # Your target is ~08:08. We check a window of 07:30 - 09:00
                if "07:30" < arrival_time < "09:00":
                    print(f">> 🎯 MATCH FOUND! Checking price for ID {journey_id}...")
                    check_prices(journey_id, arrival_time)
                    found_target = True

        if not found_target:
            print(">> Trains found, but none in the 07:30-09:00 arrival window.")

    except Exception as e:
        print(f"!! Script Crash: {e}")

def check_prices(journey_id, arrival_time):
    # STEP 3: CHECK OFFERS
    url_offers = f"https://prod-api.adp.sj.se/public/sales/booking/v3/departures/{journey_id}/offers"
    
    try:
        resp = requests.get(url_offers, headers=HEADERS)
        if resp.status_code == 200:
            data = resp.json()
            
            # Check availability (seat or bed)
            is_available = data.get("available", False)
            price = "Unknown"
            
            # Try to grab the lowest price
            try:
                price = data["priceFrom"]["price"]
            except:
                pass

            if is_available:
                msg = (f"🚨 <b>TICKETS FOUND!</b>\n"
                       f"🚂 Arrives: {arrival_time}\n"
                       f"💰 Price: {price} SEK\n"
                       f"📅 Date: {DATE}\n"
                       f"👉 <a href='https://www.sj.se'>Book Now</a>")
                send_telegram_alert(msg)
                print(">> Alert sent!")
            else:
                print(">> Train found but marked as unavailable.")
    except Exception as e:
        print(f"!! Price check error: {e}")

if __name__ == "__main__":
    check_tickets()