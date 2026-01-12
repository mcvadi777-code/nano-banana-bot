import telebot
import requests
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import time

BOT_TOKEN = os.environ["BOT_TOKEN"]
REPLICATE_API_TOKEN = os.environ["REPLICATE_API_TOKEN"]

bot = telebot.TeleBot(BOT_TOKEN)

# =======================
# Fake web server for Render
# =======================
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Nano Banana bot alive")

def start_web():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

# =======================
# Replicate (Nano Banana style)
# =======================
HEADERS = {
    "Authorization": f"Token {REPLICATE_API_TOKEN}",
    "Content-Type": "application/json"
}

def generate_image(image_url):
    r = requests.post(
        "https://api.replicate.com/v1/predictions",
        headers=HEADERS,
        json={
            "version": "black-forest-labs/flux-dev",
            "input": {
                "image": image_url,
                "prompt": "cinematic black and white dramatic portrait, ultra realistic, nano banana style, studio lighting, 8k"
            }
        }
    )

    pid = r.json()["id"]

    while True:
        res = requests.get(
            f"https://api.replicate.com/v1/predictions/{pid}",
            headers=HEADERS
        ).json()

        if res["status"] == "succeeded":
            return res["output"][0]

        if res["status"] == "failed":
            raise Exception("Generation failed")

        time.sleep(2)

# =======================
# Telegram
# =======================
@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

    bot.send_message(message.chat.id, "🍌 Nano-Banana работает…")

    try:
        img = generate_image(url)
        bot.send_photo(message.chat.id, img)
    except Exception as e:
        bot.send_message(message.chat.id, str(e))

# =======================
# Start
# =======================
if __name__ == "__main__":
    threading.Thread(target=start_web).start()
    bot.infinity_polling()
