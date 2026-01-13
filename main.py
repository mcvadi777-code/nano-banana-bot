import telebot
import requests
import os
import time
import base64

BOT_TOKEN = os.environ.get("BOT_TOKEN")
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")

if not BOT_TOKEN or not REPLICATE_API_TOKEN:
    raise RuntimeError("Missing BOT_TOKEN or REPLICATE_API_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)

HEADERS = {
    "Authorization": f"Token {REPLICATE_API_TOKEN}",
    "Content-Type": "application/json"
}

MODEL_VERSION = "c7c6d44c90f0c5a56d9c0e5d2bbf5f21d04d06fd2f3ad6ac0c2fca5d4f84e2a4"  # nano-banana

user_prompts = {}


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🍌 *Nano-Banana Pro*\n\n"
        "Отправь мне фото.\n"
        "Потом напиши, *как его изменить* (например: `cinematic black and white portrait`).",
        parse_mode="Markdown"
    )


@bot.message_handler(content_types=["text"])
def text_handler(message):
    user_prompts[message.chat.id] = message.text
    bot.send_message(message.chat.id, "🖼 Теперь отправь фото.")


@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    try:
        chat_id = message.chat.id
        prompt = user_prompts.get(chat_id, "cinematic ultra realistic portrait")

        bot.send_message(chat_id, "⏳ Обрабатываю изображение...")

        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file = requests.get(
            f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
        ).content

        img64 = base64.b64encode(file).decode()

        payload = {
            "version": MODEL_VERSION,
            "input": {
                "image": f"data:image/jpeg;base64,{img64}",
                "prompt": prompt
            }
        }

        r = requests.post(
            "https://api.replicate.com/v1/predictions",
            json=payload,
            headers=HEADERS,
            timeout=30
        )

        pred = r.json()
        get_url = pred["urls"]["get"]

        # Ждём результат
        while True:
            res = requests.get(get_url, headers=HEADERS).json()
            if res["status"] == "succeeded":
                image_url = res["output"][0]
                break
            if res["status"] == "failed":
                raise Exception("Generation failed")
            time.sleep(1.5)

        img = requests.get(image_url).content
        bot.send_photo(chat_id, img)

    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка: {e}")


bot.infinity_polling(skip_pending=True)
