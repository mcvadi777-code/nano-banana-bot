import telebot
import requests
import os
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

BOT_TOKEN = os.environ["BOT_TOKEN"]
REPLICATE_API_TOKEN = os.environ["REPLICATE_API_TOKEN"]

bot = telebot.TeleBot(BOT_TOKEN)

# ================== Fake Web Server (Render hack) ==================
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Nano Banana Bot Alive")

def start_web():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

threading.Thread(target=start_web, daemon=True).start()

# ================== Replicate ==================
HEADERS = {
    "Authorization": f"Token {REPLICATE_API_TOKEN}",
    "Content-Type": "application/json"
}

MODEL = "black-forest-labs/flux-dev"

def generate_image(image_url):
    payload = {
        "version": "black-forest-labs/flux-dev",
        "input": {
            "image": image_url,
            "prompt": (
                "cinematic black and white portrait, dramatic studio lighting, "
                "ultra realistic, high detail, preserve the original person's face, "
                "same identity, same age, same gender, no change of person"
            ),
            "image_strength": 0.8,
            "guidance_scale": 7,
            "num_inference_steps": 35
        }
    }

    r = requests.post(
        "https://api.replicate.com/v1/predictions",
        headers=HEADERS,
        json=payload
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

# ================== Telegram ==================
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "📸 Пришли фото — я превращу его в Nano-Banana портрет с сохранением лица"
    )

@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    image_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

    bot.send_message(message.chat.id, "🍌 Создаю портрет…")

    try:
        img = generate_image(image_url)
        bot.send_photo(message.chat.id, img)
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")

bot.infinity_polling()
