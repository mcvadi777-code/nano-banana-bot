import telebot
import requests
import base64
import os
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

BOT_TOKEN = os.environ["BOT_TOKEN"]
REPLICATE_API_TOKEN = os.environ["REPLICATE_API_TOKEN"]

bot = telebot.TeleBot(BOT_TOKEN)

HEADERS = {
    "Authorization": f"Token {REPLICATE_API_TOKEN}",
    "Content-Type": "application/json"
}

MODEL = "black-forest-labs/flux-dev"


# ===== Fake Web Server for Render =====
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Nano-Banana bot is running")


def run_web():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()


# ===== Replicate Image Generation =====
def generate_image(image_url):
    data = {
        "version": "latest",
        "input": {
            "image": image_url,
            "prompt": "cinematic black and white dramatic portrait, ultra realistic, sharp details, nano banana style, studio lighting, 8k"
        }
    }

    r = requests.post(
        "https://api.replicate.com/v1/predictions",
        headers=HEADERS,
        json=data
    )

    pred = r.json()
    pid = pred["id"]

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


@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

    bot.send_message(message.chat.id, "🍌 Nano-Banana генерирует…")

    try:
        img_url = generate_image(file_url)
        bot.send_photo(message.chat.id, img_url)
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")


# ===== Start everything =====
if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    bot.infinity_polling()
