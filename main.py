import telebot
import os
import requests
import time
from flask import Flask, request

BOT_TOKEN = os.environ["BOT_TOKEN"]
REPLICATE_KEY = os.environ["REPLICATE_API_TOKEN"]

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

HEADERS = {
    "Authorization": f"Token {REPLICATE_KEY}",
    "Content-Type": "application/json"
}

USER_STATE = {}

STYLES = {
    "🎥 Кино": "cinematic lighting, dramatic shadows, film look",
    "🖤 ЧБ": "black and white, high contrast, cinematic portrait",
    "🎨 Арт": "digital art, ultra detailed, artistic",
    "📸 Реализм": "photorealistic, natural lighting"
}

# =========================
# Telegram handlers
# =========================

@bot.message_handler(commands=["start"])
def start(m):
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for k in STYLES:
        kb.add(k)
    kb.add("✍️ Свой промт")

    bot.send_message(m.chat.id, "Выбери стиль или введи свой промт:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text in STYLES)
def style(m):
    USER_STATE[m.chat.id] = {"prompt": STYLES[m.text]}
    bot.send_message(m.chat.id, "Отправь фото.")

@bot.message_handler(func=lambda m: m.text == "✍️ Свой промт")
def custom_prompt(m):
    USER_STATE[m.chat.id] = {"custom": True}
    bot.send_message(m.chat.id, "Напиши промт:")

@bot.message_handler(func=lambda m: USER_STATE.get(m.chat.id, {}).get("custom") and not m.content_type == "photo")
def save_prompt(m):
    USER_STATE[m.chat.id]["prompt"] = m.text
    USER_STATE[m.chat.id]["custom"] = False
    bot.send_message(m.chat.id, "Теперь отправь фото.")

@bot.message_handler(content_types=["photo"])
def photo(m):
    if m.chat.id not in USER_STATE or "prompt" not in USER_STATE[m.chat.id]:
        bot.send_message(m.chat.id, "Сначала выбери стиль или введи промт.")
        return

    bot.send_message(m.chat.id, "⏳ Генерирую...")

    file_id = m.photo[-1].file_id
    file_info = bot.get_file(file_id)
    image_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

    try:
        out = generate(image_url, USER_STATE[m.chat.id]["prompt"])
        bot.send_photo(m.chat.id, out)
    except Exception as e:
        bot.send_message(m.chat.id, f"Ошибка генерации: {e}")

# =========================
# Nano-Banana генератор
# =========================

def generate(image_url, style):
    payload = {
        "model": "black-forest-labs/flux-schnell",
        "input": {
            "image": image_url,
            "prompt": f"{style}, nano banana style, preserve face, same person, ultra detailed portrait",
            "strength": 0.75
        }
    }

    r = requests.post("https://api.replicate.com/v1/predictions", headers=HEADERS, json=payload)
    data = r.json()

    if "id" not in data:
        raise Exception(str(data))

    pid = data["id"]

    while True:
        res = requests.get(f"https://api.replicate.com/v1/predictions/{pid}", headers=HEADERS).json()

        if res["status"] == "succeeded":
            return res["output"][0]

        if res["status"] == "failed":
            raise Exception("Nano-Banana generation failed")

        time.sleep(2)

# =========================
# Webhook
# =========================

@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "OK", 200

@app.route("/")
def home():
    return "Nano Banana bot is running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
