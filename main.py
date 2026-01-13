import os
import requests
import telebot
import replicate
from flask import Flask, request
from telebot.types import Update

BOT_TOKEN = os.environ["BOT_TOKEN"]
REPLICATE_KEY = os.environ["REPLICATE_API_TOKEN"]

bot = telebot.TeleBot(BOT_TOKEN)
replicate_client = replicate.Client(api_token=REPLICATE_KEY)

user_prompts = {}

# -------------------
# Telegram Handlers
# -------------------

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id,
        "🍌 Nano-Banana\n\n"
        "1️⃣ Напиши, как изменить фото\n"
        "2️⃣ Потом отправь изображение\n\n"
        "Например:\n«Сделай кинематографичный чёрно-белый портрет»"
    )

@bot.message_handler(content_types=["text"])
def handle_text(message):
    user_prompts[message.chat.id] = message.text
    bot.send_message(message.chat.id, "✅ Принято. Теперь отправь фото.")

@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    try:
        if message.chat.id not in user_prompts:
            bot.send_message(message.chat.id, "❗ Сначала напиши, что нужно сделать с фото.")
            return

        prompt = user_prompts[message.chat.id]

        file_info = bot.get_file(message.photo[-1].file_id)
        photo_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

        bot.send_message(message.chat.id, "🎨 Обрабатываю изображение...")

        output = replicate_client.run(
            "cjwbw/nano-banana:latest",
            input={
                "image": photo_url,
                "prompt": prompt
            }
        )

        result_url = output[0]

        bot.send_photo(message.chat.id, result_url)
        del user_prompts[message.chat.id]

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

# -------------------
# Webhook Server
# -------------------

app = Flask(__name__)

@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/")
def home():
    return "Nano-Banana bot is running"

# -------------------
# Start Webhook
# -------------------

bot.remove_webhook()
bot.set_webhook(url=f"https://nano-banana-bot-hapn.onrender.com/webhook/{BOT_TOKEN}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
