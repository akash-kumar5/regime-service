import os
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")

def send_message(chat_id: int, text: str):
    if not BOT_TOKEN:
        # print("[ERROR] BOT_TOKEN not set in worker env")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }

    try:
        resp = requests.post(url, json=payload, timeout=5)
        print(f"[DEBUG] Telegram response ({chat_id}):", resp.status_code, resp.text)
    except Exception as e:
        print("[ERROR] Telegram send failed:", e)
