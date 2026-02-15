import os

# --- TRIP CONFIGURATION ---
# Target travel date
DATE = "2026-08-20" 

# Station IDs (Default: Arlanda C -> Gällivare C)
ORIGIN_ID = "740000556" 
DESTINATION_ID = "740000254"

# --- NOTIFICATION CONFIGURATION ---
# SET THIS TO 'True' ONCE TO TEST TELEGRAM, THEN SET BACK TO 'False'
TEST_TELEGRAM = False

# Secrets (retrieved from environment variables)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
SJ_API_KEY = os.environ.get("SJ_API_KEY")
