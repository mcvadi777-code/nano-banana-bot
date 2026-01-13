import os
import time
import threading
import replicate
import telebot
from flask import Flask, request

BOT_TOKEN = os.environ["BOT_TOKEN"]
REPLICATE_KEY = os.environ["REPLICATE_API_TOKEN"]
os.environ["REPLICATE_API_TOKEN"] = REPLICATE_KEY

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

user_state = {}

STYLES = {
    "🍌 Nano-Banana": "Nano-Banana cinematic style, ultra detailed",
    "🎥 Cinema": "cinematic lighting, dramatic, film look",
    "📸 Realistic": "hyper realistic, sharp, photo quality",
    "🎨 Art": "digital painting, concept art, detailed"
}

MODEL = "db21e45d3f702bbde11fd8c1c50b9e38b0b9c7e4fdc16f8fa1f53e8d0f41c71d"


# ===========================
# START
# ===========================
@bot.message_handler(commands=["start"])
def start(msg):
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🎨 Выбрать стиль", "✍ Свой промт")
    bot.send_message(msg.chat.id,
        "🍌 Nano-Banana AI\n\n"
        "1️⃣ Выбери стиль\n"
        "2️⃣ Пришли фото\n\n"
        "Можно добавить свой текстовый промт.",
        reply_markup=kb
    )
    user_state[msg.chat.id] = {"style": STYLES["🍌 Nano-Banana"], "prompt": ""}


# ===========================
# BUTTONS
# ===========================
@bot.message_handler(func=lambda m: m.text == "🎨 Выбрать стиль")
def choose_style(msg):
    kb = telebot.types.InlineKeyboardMarkup()
    for k in STYLES:
        kb.add(telebot.types.InlineKeyboardButton(k, callback_data=k))
    bot.send_message(msg.chat.id, "Выбери стиль:", reply_markup=kb)


@bot.callback_query_handler(func=lambda call: call.data in STYLES)
def style_selected(call):
    user_state.setdefault(call.message.chat.id, {})
    user_state[call.message.chat.id]["style"] = STYLES[call.data]
    bot.send_message(call.message.chat.id, f"Стиль выбран: {call.data}")


@bot.message_handler(func=lambda m: m.text == "✍ Свой промт")
def ask_prompt(msg):
    bot.send_message(msg.chat.id, "Напиши свой текст для обработки изображения.")


@bot.message_handler(content_types=["text"])
def save_prompt(msg):
    if msg.text.startswith("/"):
        return
    user_state.setdefault(msg.chat.id, {})
    user_state[msg.chat.id]["prompt"] = msg.text
    bot.send_message(msg.chat.id, "Промт сохранён. Теперь пришли фото.")


# ===========================
# PHOTO
# ===========================
@bot.message_handler(content_types=["photo"])
def photo(msg):
    bot.send_message(msg.chat.id, "📥 Фото получено. Запускаю Nano-Banana…")

    file_id = msg.photo[-1].file_id
    file_info = bot.get_file(file_id)
    url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

    state = user_state.get(msg.chat.id, {})
    style = state.get("style", STYLES["🍌 Nano-Banana"])
    prompt = state.get("prompt", "")

    full_prompt = f"{style}. {prompt}"

    threading.Thread(target=process, args=(msg.chat.id, url, full_prompt)).start()


# ===========================
# PROCESS
# ===========================
def process(chat_id, image_url, prompt):
    try:
        bot.send_message(chat_id, "🍌 Nano-Banana работает…")

        prediction = replicate.predictions.create(
            version=MODEL,
            input={
                "image": image_url,
                "prompt": prompt
            }
        )

        while prediction.status not in ["succeeded", "failed"]:
            time.sleep(1)
            prediction = replicate.predictions.get(prediction.id)

        if prediction.status == "failed":
            bot.send_message(chat_id, "❌ Ошибка генерации.")
            return

        output = prediction.output
        img = output[0] if isinstance(output, list) else output

        bot.send_photo(chat_id, img)

    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка: {e}")


# ===========================
# WEBHOOK
# ===========================
@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(data)
    bot.process_new_updates([update])
    return "ok", 200


@app.route("/")
def index():
    return "Nano-Banana AI bot online"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
