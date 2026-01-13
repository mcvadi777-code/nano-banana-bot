import os
import telebot
import requests
from flask import Flask, request

BOT_TOKEN = os.environ.get("BOT_TOKEN")
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")

if not BOT_TOKEN or not REPLICATE_API_TOKEN or not RENDER_EXTERNAL_URL:
    raise Exception("Missing environment variables")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

REPLICATE_URL = "https://api.replicate.com/v1/predictions"
HEADERS = {
    "Authorization": f"Token {REPLICATE_API_TOKEN}",
    "Content-Type": "application/json"
}

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "📸 Пришли фото — я превращу его в Nano-Banana стиль.")

@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    try:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        photo_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

        payload = {
            "version": "da0e3c3c1f7f21f85e8c1e8a2b8a39c1c7ad79c3e8c8c2b12ef9d0d9a96a7e8d",
            "input": {
                "image": photo_url,
                "prompt": "cinematic black and white nano banana style portrait"
            }
        }

        r = requests.post(REPLICATE_URL, headers=HEADERS, json=payload)
        pred = r.json()

        if "id" not in pred:
            bot.send_message(message.chat.id, "❌ Ошибка генерации")
            return

        prediction_id = pred["id"]

        # wait result
        while True:
            res = requests.get(f"{REPLICATE_URL}/{prediction_id}", headers=HEADERS).json()
            if res["status"] == "succeeded":
                image_url = res["output"][0]
                bot.send_photo(message.chat.id, image_url)
                break
            elif res["status"] == "failed":
                bot.send_message(message.chat.id, "❌ Генерация не удалась")
                break

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/")
def home():
    return "Nano Banana bot is running"

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_EXTERNAL_URL}/webhook/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=10000)
