import telebot
import requests
import base64
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Fake HTTP server for Render Free
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

BOT_TOKEN = os.environ["BOT_TOKEN"]
GEMINI_KEY = os.environ["GEMINI_KEY"]

bot = telebot.TeleBot(BOT_TOKEN)

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash-image:generateContent?key={GEMINI_KEY}"

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "📸 Отправь фото — я сделаю кинематографичный чёрно-белый портрет"
    )

@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    try:
        bot.send_message(message.chat.id, "🎨 Обрабатываю...")

        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file = requests.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}")

        img64 = base64.b64encode(file.content).decode()

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": "Create a cinematic black and white portrait, dramatic lighting, keep the face realistic and recognizable"},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": img64
                            }
                        }
                    ]
                }
            ]
        }

        r = requests.post(GEMINI_URL, json=payload, timeout=90)

        if r.status_code != 200 or not r.text:
            bot.send_message(message.chat.id, f"Gemini HTTP error {r.status_code}")
            return

        try:
            j = r.json()
        except:
            bot.send_message(message.chat.id, f"Gemini invalid response:\n{r.text}")
            return

        if "candidates" not in j:
            bot.send_message(message.chat.id, f"Gemini error:\n{j}")
            return

        parts = j["candidates"][0]["content"]["parts"]

        image_data = None
        for p in parts:
            if "inlineData" in p:
                image_data = p["inlineData"]["data"]

        if not image_data:
            bot.send_message(message.chat.id, f"Gemini returned no image:\n{j}")
            return

        bot.send_photo(message.chat.id, base64.b64decode(image_data))

    except Exception as e:
        bot.send_message(message.chat.id, f"Error: {e}")

bot.infinity_polling()
