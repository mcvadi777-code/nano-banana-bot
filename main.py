import os
import telebot
import requests
import base64
from flask import Flask, request

BOT_TOKEN = os.environ["BOT_TOKEN"]
GEMINI_KEY = os.environ["GEMINI_KEY"]

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- TELEGRAM HANDLERS ---

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🍌 *Nano-Banana Bot*\n\n"
        "Отправь фото и напиши промт.\n"
        "Пример: _Сделай кинематографичный чёрно-белый портрет_",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: True, content_types=["text"])
def save_prompt(message):
    bot.send_message(message.chat.id, "Теперь отправь фото 📸")
    bot.user_prompt = message.text

@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    try:
        prompt = getattr(bot, "user_prompt", "Make a cinematic nano-banana style portrait")

        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file = requests.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}")

        img64 = base64.b64encode(file.content).decode()

        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash-image:generateContent?key={GEMINI_KEY}"

        data = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {
                        "mime_type": "image/jpeg",
                        "data": img64
                    }}
                ]
            }]
        }

        r = requests.post(url, json=data)
        r.raise_for_status()

        result = r.json()
        img = result["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]

        bot.send_photo(message.chat.id, base64.b64decode(img))

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

# --- WEBHOOK ---

@app.route("/webhook/" + BOT_TOKEN, methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def home():
    return "Nano-Banana Bot is alive 🍌"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
