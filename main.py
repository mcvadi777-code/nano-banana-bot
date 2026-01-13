import telebot
import requests
import os
import time

BOT_TOKEN = os.environ["BOT_TOKEN"]
REPLICATE_API_TOKEN = os.environ["REPLICATE_API_TOKEN"]

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

WEBHOOK_URL = "https://nano-banana-bot.onrender.com/webhook"

user_style = {}

HEADERS = {
    "Authorization": f"Token {REPLICATE_API_TOKEN}",
    "Content-Type": "application/json"
}

# ---------- MENU ----------
def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🎥 Кино", "🖤 Ч/Б")
    markup.row("🎨 Арт", "👤 Сохранить лицо")
    return markup

# ---------- WEBHOOK SETUP ----------
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "Выбери стиль, потом пришли фото:",
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda m: m.text in ["🎥 Кино", "🖤 Ч/Б", "🎨 Арт", "👤 Сохранить лицо"])
def set_style(message):
    styles = {
        "🎥 Кино": "cinematic movie lighting, dramatic shadows",
        "🖤 Ч/Б": "black and white dramatic portrait",
        "🎨 Арт": "artistic painterly style",
        "👤 Сохранить лицо": "realistic portrait, preserve identity"
    }
    user_style[message.chat.id] = styles[message.text]
    bot.send_message(message.chat.id, "Стиль сохранён. Теперь пришли фото 📸")

# ---------- IMAGE GENERATION ----------
def generate(image_url, style):
    payload = {
        "version": "black-forest-labs/flux-dev",
        "input": {
            "image": image_url,
            "prompt": style + ", preserve face, same person, ultra detailed",
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

@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    style = user_style.get(message.chat.id, "cinematic portrait")

    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    image_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

    bot.send_message(message.chat.id, "🍌 Генерирую...")

    try:
        img = generate(image_url, style)
        bot.send_photo(message.chat.id, img)
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")

# ---------- WEBHOOK ENDPOINT ----------
from flask import Flask, request

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

# ---------- START ----------
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
