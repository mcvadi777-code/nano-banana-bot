import telebot
import requests
import base64
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- Fake HTTP server for Render Free ---
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
# --------------------------------------

BOT_TOKEN = os.environ["BOT_TOKEN"]
GEMINI_KEY = os.environ["GEMINI_KEY"]

bot = telebot.TeleBot(BOT_TOKEN)

def nano_banana_edit(image_bytes):
    img64 = base64.b64encode(image_bytes).decode()

    url = f"https://generativelanguage.googleapis.com/v1beta/images:edit?key={GEMINI_KEY}"

    payload = {
        "model": "nano-banana-3-pro",
        "image": {
            "mimeType": "image/jpeg",
            "data": img64
        },
        "prompt": "cinematic black and white portrait, dramatic lighting, realistic face, high detail"
    }

    r = requests.post(url, json=payload, timeout=60)
    j = r.json()

    if "image" not in j:
        return None, j

    return base64.b64decode(j["image"]["data"]), None


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Отправь фото — я превращу его в кинематографичный чёрно-белый портрет 📸")


@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    try:
        bot.send_message(message.chat.id, "🎨 Обрабатываю...")

        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file = requests.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}")

        image, error = nano_banana_edit(file.content)

        if error:
            bot.send_message(message.chat.id, f"Nano-Banana error:\n{error}")
            return

        bot.send_photo(message.chat.id, image)

    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")

bot.infinity_polling()
