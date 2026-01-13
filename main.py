import os
import telebot
from flask import Flask, request

BOT_TOKEN = os.environ["BOT_TOKEN"]

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Команда /start
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "📸 Пришли фото — я превращу его в Nano-Banana стиль.")

# Telegram будет присылать сюда JSON
@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

# Render пингует /
@app.route("/", methods=["GET"])
def index():
    return "Nano Banana bot is running", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
