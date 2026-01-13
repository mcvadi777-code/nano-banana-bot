import telebot
import requests
import os
import time

BOT_TOKEN = os.environ["BOT_TOKEN"]
REPLICATE_KEY = os.environ["REPLICATE_KEY"]

bot = telebot.TeleBot(BOT_TOKEN)

headers = {
    "Authorization": f"Token {REPLICATE_KEY}",
    "Content-Type": "application/json"
}

user_prompt = {}

@bot.message_handler(commands=["start"])
def start(msg):
    bot.send_message(
        msg.chat.id,
        "🍌 Nano-Banana Bot\n\n"
        "1️⃣ Напиши, как изменить фото (например: «киношный чб портрет»)\n"
        "2️⃣ Потом отправь фото"
    )

@bot.message_handler(content_types=["text"])
def save_prompt(msg):
    user_prompt[msg.chat.id] = msg.text
    bot.send_message(msg.chat.id, "📸 Теперь отправь фото.")

def upload_to_telegraph(image_bytes):
    r = requests.post(
        "https://telegra.ph/upload",
        files={"file": ("image.jpg", image_bytes)}
    )
    return "https://telegra.ph" + r.json()[0]["src"]

@bot.message_handler(content_types=["photo"])
def handle_photo(msg):
    try:
        prompt = user_prompt.get(msg.chat.id)
        if not prompt:
            bot.send_message(msg.chat.id, "Сначала напиши, как изменить изображение.")
            return

        # 1. Скачать фото из Telegram
        file_id = msg.photo[-1].file_id
        file_info = bot.get_file(file_id)
        image_bytes = requests.get(
            f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
        ).content

        # 2. Залить на telegra.ph чтобы получить URL
        image_url = upload_to_telegraph(image_bytes)

        # 3. Отправить в Nano-Banana через Replicate
        payload = {
            "version": "lucataco/nano-banana",
            "input": {
                "image": image_url,
                "prompt": prompt
            }
        }

        r = requests.post(
            "https://api.replicate.com/v1/predictions",
            json=payload,
            headers=headers,
            timeout=30
        )

        data = r.json()
        prediction_id = data["id"]

        # 4. Ждём результат
        while True:
            status = requests.get(
                f"https://api.replicate.com/v1/predictions/{prediction_id}",
                headers=headers
            ).json()

            if status["status"] == "succeeded":
                result_image = status["output"][0]   # Replicate всегда возвращает список URL
                bot.send_photo(msg.chat.id, result_image)
                return

            if status["status"] == "failed":
                bot.send_message(msg.chat.id, "❌ Генерация не удалась.")
                return

            time.sleep(2)

    except Exception as e:
        bot.send_message(msg.chat.id, f"❌ Ошибка: {e}")

bot.infinity_polling(skip_pending=True)
