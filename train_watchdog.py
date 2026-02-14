import requests
import json
import os
import sys
import time
from datetime import datetime

# --- CONFIGURATION ---
# 1. Target Date
DATE = "2026-08-20" 

# 2. Stations (Arlanda C -> Gällivare C)
ORIGIN_ID = "740000556" 
DESTINATION_ID = "740000254"

# 3. SET THIS TO 'True' ONCE TO TEST TELEGRAM, THEN SET BACK TO 'False'
TEST_TELEGRAM = False

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
        print(f"!! TELEGRAM NOT CONFIGURED. Message was: {message}")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"!! Telegram Error: {e}")

def check_tickets():
    # --- 0. TELEGRAM CONNECTION TEST ---
    if TEST_TELEGRAM:
        print(">> Sending Test Message to Telegram...")
        send_telegram_alert("🔔 <b>Test Message:</b> The Watchdog is connected!")

    print(f"--- Checking Night Train: {DATE} ---")

    # --- 1. INITIATE SEARCH ---
    url_init = "https://prod-api.adp.sj.se/public/sales/booking/v3/search"
    payload = {
        "origin": ORIGIN_ID,
        "destination": DESTINATION_ID,
        "departureDate": DATE,
        "passengers": [{"passengerCategory": {"type": "ADULT"}}, {"passengerCategory": {"type": "ADULT"}}]
    }

    try:
        resp1 = requests.post(url_init, headers=HEADERS, json=payload)
        if resp1.status_code != 200:
            print(f"!! Init failed: {resp1.status_code}")
            return

        search_id = resp1.json().get("departureSearchId")
        if not search_id:
            print("!! No search ID returned.")
            return

        print(f">> Session: {search_id}")
        time.sleep(1) 

        # --- 2. FETCH TIMETABLE ---
        url_results = f"https://prod-api.adp.sj.se/public/sales/booking/v3/departures/search/{search_id}"
        resp2 = requests.get(url_results, headers=HEADERS)
        
        if resp2.status_code != 200:
            print(f"!! Fetch failed: {resp2.status_code}")
            return

        data = resp2.json()
        travels = data.get("travels", [])
        
        if not travels:
            print(">> No trains found yet (Schedule likely not released).")
            # If it's Monday, send a heartbeat "I'm alive" message
            if datetime.now().weekday() == 0: 
                send_telegram_alert(f"🗓 <b>Weekly Report:</b>\nChecking {DATE}.\nStatus: Schedule not released yet.")
            return

        departures = travels[0].get("departures", [])
        print(f">> Scanned {len(departures)} trains.")
        
        found_target = False
        night_train_warnings = []

        for dep in departures:
            arrival_iso = dep.get("arrivalDateTime")
            if not arrival_iso: continue

            arrival_time = datetime.fromisoformat(arrival_iso).strftime("%H:%M")
            
            # Target Window: 07:30 - 09:00 (Night Train)
            if "07:30" < arrival_time < "09:00":
                journey_id = dep.get("departureId")
                
                # CHECK WARNINGS (e.g., POTENTIAL_MAINT)
                reasons = dep.get("unavailableReasons", [])
                warnings = [r.get("code") for r in reasons]
                
                print(f">> 🎯 MATCH! Arrives {arrival_time}.")
                if warnings:
                    print(f"   ⚠️ WARNINGS: {warnings}")
                    night_train_warnings = warnings
                
                check_prices(journey_id, arrival_time)
                found_target = True

        # --- WEEKLY HEARTBEAT (MONDAYS ONLY) ---
        # If we didn't find tickets, but it's Monday, send a status update.
        if not found_target and datetime.now().weekday() == 0:
            status_msg = f"🗓 <b>Weekly Report:</b>\nChecking {DATE}.\n"
            if night_train_warnings:
                status_msg += f"Status: Train found but blocked: {', '.join(night_train_warnings)}"
            else:
                status_msg += "Status: Night Train not in list yet."
            
            send_telegram_alert(status_msg)
            print(">> Weekly heartbeat sent.")

    except Exception as e:
        print(f"!! Critical Error: {e}")

def check_prices(journey_id, arrival_time):
    # --- 3. CHECK PRICES ---
    url_offers = f"https://prod-api.adp.sj.se/public/sales/booking/v3/departures/{journey_id}/offers"
    
    try:
        resp = requests.get(url_offers, headers=HEADERS)
        if resp.status_code == 200:
            data = resp.json()
            is_available = data.get("available", False)
            
            if is_available:
                price = "Unknown"
                try:
                    price = data["priceFrom"]["price"]
                except: pass

                msg = (f"🚨 <b>TICKETS RELEASED!</b>\n"
                       f"🚂 <b>Night Train Found</b>\n"
                       f"📅 Date: {DATE}\n"
                       f"🏁 Arrive: {arrival_time}\n"
                       f"💰 Price: {price} SEK\n"
                       f"👉 <a href='https://www.sj.se'>Buy Now</a>")
                
                send_telegram_alert(msg)
                print(">> TELEGRAM SENT! Tickets are bookable.")
            else:
                print(">> Train found, but tickets are not released/bookable yet.")
    except Exception as e:
        print(f"!! Error checking price: {e}")

if __name__ == "__main__":
    check_tickets()