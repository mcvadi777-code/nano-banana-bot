import os
import telebot
import requests
from flask import Flask, request

BOT_TOKEN = os.environ["BOT_TOKEN"]

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# /start
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "📸 Пришли фото — я превращу его в Nano-Banana стиль.")

# ОБРАБОТЧИК ФОТО
@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    try:
        bot.send_message(message.chat.id, "🍌 Фото получено. Обрабатываю...")

        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)

        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
        img = requests.get(file_url).content

        # Пока просто отправим его обратно как тест
        bot.send_photo(message.chat.id, img, caption="✅ Фото дошло до сервера. Следующий шаг — Nano-Banana.")

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

# Webhook
@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/", methods=["GET"])
def index():
    return "Nano Banana bot is running", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
