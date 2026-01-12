import telebot
import requests
import base64
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
GEMINI_KEY = os.environ["GEMINI_KEY"]

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(content_types=["photo"])
def handle(message):
    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    file = requests.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}")

    img64 = base64.b64encode(file.content).decode()

    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash-image:generateContent?key={GEMINI_KEY}"

    data = {
        "contents": [{
            "parts": [
                {"text": "Make a cinematic black and white portrait"},
                {"inline_data": {
                    "mime_type": "image/jpeg",
                    "data": img64
                }}
            ]
        }]
    }

    r = requests.post(url, json=data)
    img = r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]

    bot.send_photo(message.chat.id, base64.b64decode(img))

bot.infinity_polling()
