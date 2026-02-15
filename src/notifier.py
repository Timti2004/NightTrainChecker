import requests
import config

class TelegramNotifier:
    """Handles sending notifications via the Telegram Bot API."""
    
    def __init__(self):
        self.token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.url = f"https://api.telegram.org/bot{self.token}/sendMessage" if self.token else None

    def send(self, message):
        """Sends an HTML formatted message to the configured Telegram chat."""
        if not self.token or not self.chat_id:
            print(f"!! TELEGRAM NOT CONFIGURED. Message was: {message}")
            return
        
        payload = {
            "chat_id": self.chat_id, 
            "text": message, 
            "parse_mode": "HTML"
        }
        
        try:
            response = requests.post(self.url, json=payload)
            response.raise_for_status()
        except Exception as e:
            print(f"!! Telegram Error: {e}")
