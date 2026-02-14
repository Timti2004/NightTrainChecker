import requests
import json
import os
import sys
import time
from datetime import datetime

# --- CONFIGURATION ---
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

    url_init = "https://prod-api.adp.sj.se/public/sales/booking/v3/search"
    
    # 🔍 CHANGED: We now send the EXACT passenger structure from your logs
    # Including all the nulls and false values to keep the server happy.
    payload = {
        "journeyDate": {
            "date": DATE,
            "time": "00:00"
        },
        "origin": {
            "uicStationCode": ORIGIN_ID,
            "name": "Arlanda Flygplats",
            "shortName": None  # Added
        },
        "destination": {
            "uicStationCode": DESTINATION_ID,
            "name": "Gällivare C/Resecentrum",
            "shortName": "Gällivare C/Rc" # Matches your log
        },
        "passengers": [
            {
                "id": "passenger_1",
                "passengerCategory": {
                    "type": "ADULT",
                    "age": None  # Matches your log (null)
                },
                "personalInformationIsMasked": False,
                "firstName": None,
                "lastName": None,
                "earnPrioPoints": False,
                "customer": None,
                "travelPass": None,
                "specialNeed": "NO",
                "childInLap": False,
                "discountCards": []
            }
        ],
        # Added these empty filters just in case the validator needs them
        "outboundAdditionalSearchFilters": {
             "onlyDirectJourneys": None,
             "allowedServiceTypes": None,
             "excludedServiceTypes": None,
             "departureDateTime": None,
             "arrivalDateTime": None,
             "viaStations": None,
             "interchangeStations": None,
             "minTransferTimeInMinutes": None,
             "minTransferTime": None
        },
        "inboundAdditionalSearchFilters": {
             "onlyDirectJourneys": None,
             "allowedServiceTypes": None,
             "excludedServiceTypes": None,
             "departureDateTime": None,
             "arrivalDateTime": None,
             "viaStations": None,
             "interchangeStations": None,
             "minTransferTimeInMinutes": None,
             "minTransferTime": None
        },
        "promoCodes": []
    }

    try:
        # Request 1: Start Search
        resp1 = requests.post(url_init, headers=HEADERS, json=payload)
        
        if resp1.status_code != 200 and resp1.status_code != 201:
            print(f"!! Init Error {resp1.status_code}")
            print(f"Server said: {resp1.text}")
            return

        data1 = resp1.json()
        search_id = data1.get("departureSearchId")

        if not search_id:
             # Sometimes the response IS the journey list
            if "journeys" in data1:
                 process_journeys(data1["journeys"])
                 return
            print("!! No search ID. Keys:", data1.keys())
            return

        print(f">> Search initiated. ID: {search_id}")
        
        # STEP 2: Fetch Results
        time.sleep(1)
        url_results = f"https://prod-api.adp.sj.se/public/sales/booking/v3/search/{search_id}"
        resp2 = requests.get(url_results, headers=HEADERS)
        
        if resp2.status_code != 200:
            print(f"!! Fetch Error {resp2.status_code}: {resp2.text[:200]}")
            return

        data2 = resp2.json()
        journeys = data2.get("journeys", [])
        process_journeys(journeys)

    except Exception as e:
        print(f"!! Script Crash: {e}")

def process_journeys(journeys):
    if not journeys:
        print(">> Search successful, but NO journeys found (Likely not released yet).")
        return

    found_target = False
    for journey in journeys:
        try:
            arrival_iso = journey.get('arrivalDateTime')
            if not arrival_iso and 'legs' in journey:
                arrival_iso = journey['legs'][-1]['arrivalDateTime']
            
            if not arrival_iso: continue

            arrival_time = datetime.fromisoformat(arrival_iso).strftime("%H:%M")
            
            # Check for morning arrival (approx 08:24)
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
                           f"Price: {price} SEK\n"
                           f"👉 <a href='https://www.sj.se'>Buy Now</a>")
                    send_telegram_alert(msg)
                    found_target = True
        except:
            continue
    
    if not found_target:
        print(">> Train found in schedule but NOT bookable yet.")

if __name__ == "__main__":
    print("--- Starting Train Watchdog ---")
    check_tickets()