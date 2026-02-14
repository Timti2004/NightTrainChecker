import requests
import json
import os
import sys
import time
from datetime import datetime

# --- CONFIGURATION ---
# Target Departure Date
DATE = "2026-03-20" 

# Station IDs (Arlanda C -> Gällivare C)
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

def send_telegram_alert(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f">> ALERT: {message}")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"})
    except Exception as e:
        print(f"!! Telegram Error: {e}")

def check_tickets():
    print(f"--- Checking Night Train: {DATE} (Arlanda -> Gällivare) ---")

    # 1. SEARCH FOR TRAINS
    url_search = "https://prod-api.adp.sj.se/public/sales/booking/v3/search"
    payload = {
        "origin": ORIGIN_ID,
        "destination": DESTINATION_ID,
        "departureDate": DATE,
        "passengers": [{"passengerCategory": {"type": "ADULT"}}, {"passengerCategory": {"type": "ADULT"}}]
    }

    try:
        resp = requests.post(url_search, headers=HEADERS, json=payload)
        if resp.status_code != 200:
            print(f"!! Search Error {resp.status_code}: {resp.text[:200]}")
            return

        data = resp.json()
        journeys = data.get("journeys", [])

        if not journeys:
            print(">> No trains found yet (Tickets likely not released).")
            return

        print(f">> Success! Found {len(journeys)} trains in schedule.")

        # 2. FILTER FOR NIGHT TRAIN
        found_candidate = False
        for journey in journeys:
            journey_id = journey.get("id")
            
            # Extract arrival time
            arrival_iso = journey.get("arrivalDateTime")
            if not arrival_iso and "legs" in journey:
                arrival_iso = journey["legs"][-1]["arrivalDateTime"]
            
            if not arrival_iso: continue
            arrival_time = datetime.fromisoformat(arrival_iso).strftime("%H:%M")

            # DEBUG: Print every train seen so you know it works
            print(f"   - Scanned train arriving at {arrival_time}")

            # Filter: We strictly want the train arriving 08:00 - 09:30
            if "08:00" < arrival_time < "09:30":
                print(f">> 🎯 MATCH FOUND! Arrives: {arrival_time}. Checking Price...")
                check_offers(journey_id, arrival_time)
                found_candidate = True

        if not found_candidate:
            print(">> Schedule is up, but no train matches the Night Train arrival time (08:00-09:30).")

    except Exception as e:
        print(f"!! Script Crash: {e}")

def check_offers(departure_id, arrival_time):
    # 3. GET PRICE (Step 2)
    url_offers = f"https://prod-api.adp.sj.se/public/sales/booking/v3/departures/{departure_id}/offers"
    
    try:
        resp = requests.get(url_offers, headers=HEADERS)
        if resp.status_code != 200:
            print(f"!! Offers Error {resp.status_code}")
            return

        data = resp.json()
        
        is_available = False
        min_price = 99999
        currency = "SEK"

        # Check availability
        # We check both Bed and Seat offers to be safe
        for offer_type in ["bedOffers", "seatOffers"]:
            offers = data.get(offer_type, {})
            if offers.get("available"):
                is_available = True
                try:
                    p = float(offers["priceFrom"]["price"])
                    if p < min_price: min_price = p
                except: pass

        if is_available:
            msg = (f"🚨 <b>TICKETS RELEASED!</b>\n"
                   f"🚂 <b>Night Train Found</b>\n"
                   f"📅 Depart: {DATE}\n"
                   f"🏁 Arrive: {arrival_time}\n"
                   f"💰 From: {int(min_price)} {currency}\n"
                   f"👉 <a href='https://www.sj.se'>Buy Now on SJ.se</a>")
            
            print(f">> AVAILABLE! Price: {min_price}")
            send_telegram_alert(msg)
        else:
            print(f">> Train found, but marked as SOLD OUT or BLOCKED.")

    except Exception as e:
        print(f"!! Error parsing offers: {e}")

if __name__ == "__main__":
    check_tickets()
