import os
import telebot
import requests
import replicate
from flask import Flask, request

BOT_TOKEN = os.environ["BOT_TOKEN"]
REPLICATE_API_TOKEN = os.environ["REPLICATE_API_TOKEN"]

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
replicate.Client(api_token=REPLICATE_API_TOKEN)

# ================== TELEGRAM ==================

@bot.message_handler(commands=["start"])
def start(msg):
    bot.send_message(
        msg.chat.id,
        "👋 Отправь фото и напиши текст, что с ним сделать.\n\n"
        "Пример:\n"
        "Сделай в стиле Nano-Banana, чёрно-белый, киношный портрет."
    )

user_prompts = {}

@bot.message_handler(content_types=["text"])
def save_prompt(msg):
    user_prompts[msg.chat.id] = msg.text
    bot.send_message(msg.chat.id, "📝 Промт сохранён. Теперь отправь фото.")

@bot.message_handler(content_types=["photo"])
def handle_photo(msg):
    try:
        if msg.chat.id not in user_prompts:
            bot.send_message(msg.chat.id, "Сначала напиши, что нужно сделать с фото ✍️")
            return

        prompt = user_prompts[msg.chat.id]

        file_info = bot.get_file(msg.photo[-1].file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

        bot.send_message(msg.chat.id, "🎨 Обрабатываю…")

        output = replicate.run(
            "fofr/nano-banana",
            input={
                "image": file_url,
                "prompt": prompt
            }
        )

        if isinstance(output, list) and len(output) > 0:
            bot.send_photo(msg.chat.id, output[0])
        else:
            bot.send_message(msg.chat.id, "❌ Ошибка генерации")

    except Exception as e:
        bot.send_message(msg.chat.id, f"❌ Ошибка: {e}")

# ================== WEBHOOK ==================

@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_json(force=True))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def home():
    return "Nano-Banana bot is running!"

# ================== START ==================

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{os.environ['RENDER_EXTERNAL_URL']}/webhook/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=10000)
