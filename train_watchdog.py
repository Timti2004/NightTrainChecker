import requests
import json
import os
import sys
import time
from datetime import datetime

# --- CONFIGURATION ---
# Switching back to your REAL target date
DATE = "2026-03-20" 
ORIGIN_ID = "740000556"  # Arlanda Central
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
        data1 = resp1.json()
        search_id = data1.get("departureSearchId")

        if not search_id:
            print("!! Step 1 failed. No search ID.")
            return

        print(f">> Search Session Created: {search_id}")
        print(">> Waiting for timetable to generate...")
        time.sleep(2) # Give the server time to find trains

        # STEP 2: FETCH TIMETABLE (The Missing Piece)
        # Based on your previous offers.json structure, this is the correct results URL
        url_results = f"https://prod-api.adp.sj.se/public/sales/booking/v3/search/{search_id}/outbound-journeys"
        
        resp2 = requests.get(url_results, headers=HEADERS)
        
        # If the URL above fails, we try the backup variant
        if resp2.status_code == 404:
            url_results = f"https://prod-api.adp.sj.se/public/sales/booking/v3/search/{search_id}/timetable"
            resp2 = requests.get(url_results, headers=HEADERS)

        if resp2.status_code != 200:
            print(f"!! Step 2 failed ({resp2.status_code}). URL might be different.")
            return

        data2 = resp2.json()
        
        # In this API version, journeys are often under 'journeys' or 'outboundJourneys'
        journeys = data2.get("journeys") or data2.get("outboundJourneys") or []

        if not journeys:
            print(">> Timetable received, but it is empty (No trains released yet).")
            return

        print(f">> SUCCESS! Scanned {len(journeys)} journeys.")
        found_target = False

        for journey in journeys:
            # Each journey in the list has its own 'id' for prices
            journey_id = journey.get("id")
            arrival_iso = journey.get("arrivalDateTime")
            
            if not arrival_iso and "legs" in journey:
                arrival_iso = journey["legs"][-1]["arrivalDateTime"]
            
            if arrival_iso:
                arrival_time = datetime.fromisoformat(arrival_iso).strftime("%H:%M")
                print(f"   - Scanned train arriving at {arrival_time}")

                # Night train target window (08:08 in your screenshot)
                if "07:30" < arrival_time < "09:30":
                    print(f">> 🎯 MATCH FOUND! Checking price for {journey_id}...")
                    check_prices(journey_id, arrival_time)
                    found_target = True

        if not found_target:
            print(">> No morning night train found in the results.")

    except Exception as e:
        print(f"!! Script Crash: {e}")

def check_prices(journey_id, arrival_time):
    # STEP 3: CHECK ACTUAL OFFERS (The logic you confirmed earlier)
    url_offers = f"https://prod-api.adp.sj.se/public/sales/booking/v3/departures/{journey_id}/offers"
    
    resp = requests.get(url_offers, headers=HEADERS)
    if resp.status_code == 200:
        data = resp.json()
        # Logic to check availability in seatOffers or bedOffers
        can_book = data.get("available", False)
        price = data.get("priceFrom", {}).get("price", "N/A")

        if can_book:
            msg = (f"🚨 <b>TICKETS FOUND!</b>\n"
                   f"🚂 Arrives: {arrival_time}\n"
                   f"💰 Price: {price} SEK\n"
                   f"👉 <a href='https://www.sj.se'>Book Now</a>")
            send_telegram_alert(msg)
            print(">> Alert sent!")
        else:
            print(">> Train exists but currently marked as unbookable.")

if __name__ == "__main__":
    check_tickets()