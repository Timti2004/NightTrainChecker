import time
from datetime import datetime
import config
from sj_api import SJClient
from notifier import TelegramNotifier

def run_watchdog():
    notifier = TelegramNotifier()
    client = SJClient()

    if config.TEST_TELEGRAM:
        print(">> Sending Test Message to Telegram...")
        notifier.send("🔔 <b>Test Message:</b> The Watchdog is connected!")

    print(f"--- Checking Night Train: {config.DATE} ---")

    # 1. Start Search
    search_id = client.search_departures(config.ORIGIN_ID, config.DESTINATION_ID, config.DATE)
    if not search_id:
        return

    print(f">> Session: {search_id}")
    time.sleep(1) # Gentle delay for API processing

    # 2. Get Timetable
    data = client.fetch_results(search_id)
    if not data:
        return

    travels = data.get("travels", [])
    if not travels:
        print(">> No trains found yet (Schedule likely not released).")
        # Weekly Heartbeat
        if datetime.now().weekday() == 0:
            notifier.send(f"🗓 <b>Weekly Report:</b>\nChecking {config.DATE}.\nStatus: Schedule not released yet.")
        return

    departures = travels[0].get("departures", [])
    print(f">> Scanned {len(departures)} trains.")
    
    found_target = False
    night_train_warnings = []

    for dep in departures:
        arrival_iso = dep.get("arrivalDateTime")
        if not arrival_iso: continue

        arrival_time = datetime.fromisoformat(arrival_iso).strftime("%H:%M")
        
        # Filter for Night Train arrival window
        if "07:30" < arrival_time < "09:00":
            found_target = True
            journey_id = dep.get("departureId")
            
            reasons = dep.get("unavailableReasons", [])
            warnings = [r.get("code") for r in reasons]
            
            print(f">> 🎯 MATCH! Arrives {arrival_time}.")
            if warnings:
                print(f"   ⚠️ WARNINGS: {warnings}")
                night_train_warnings = warnings
            
            # 3. Check specific booking availability
            offers = client.get_offers(journey_id)
            if offers and offers.get("available"):
                price = offers.get("priceFrom", {}).get("price", "Unknown")
                msg = (f"🚨 <b>TICKETS RELEASED!</b>\n"
                       f"🚂 <b>Night Train Found</b>\n"
                       f"📅 Date: {config.DATE}\n"
                       f"🏁 Arrive: {arrival_time}\n"
                       f"💰 Price: {price} SEK\n"
                       f"👉 <a href='https://www.sj.se'>Buy Now</a>")
                notifier.send(msg)
                print(">> TELEGRAM SENT! Tickets are bookable.")
            else:
                print(">> Train found, but tickets are not released/bookable yet.")

    # Weekly report if nothing found
    if not found_target and datetime.now().weekday() == 0:
        status_msg = (f"🗓 <b>Weekly Report:</b>\n"
                      f"Checking {config.DATE}.\n")
        
        if night_train_warnings:
            status_msg += f"Status: Train found but blocked: {', '.join(night_train_warnings)}"
        else:
            status_msg += "Status: Night Train not in list yet."
        notifier.send(status_msg)
        print(">> Weekly heartbeat sent.")

if __name__ == "__main__":
    run_watchdog()
