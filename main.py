import telebot
import requests
import base64
import os
import time

BOT_TOKEN = os.environ["BOT_TOKEN"]
REPLICATE_TOKEN = os.environ["REPLICATE_API_TOKEN"]

bot = telebot.TeleBot(BOT_TOKEN)

HEADERS = {
    "Authorization": f"Token {REPLICATE_TOKEN}",
    "Content-Type": "application/json"
}

MODEL = "black-forest-labs/flux-dev"


def generate_image(image_url):
    data = {
        "version": "latest",
        "input": {
            "image": image_url,
            "prompt": "cinematic black and white dramatic portrait, ultra realistic, sharp details, nano banana style, studio lighting, 8k"
        }
    }

    r = requests.post(
        "https://api.replicate.com/v1/predictions",
        headers=HEADERS,
        json=data
    )

    pred = r.json()
    pid = pred["id"]

    # wait for generation
    while True:
        res = requests.get(
            f"https://api.replicate.com/v1/predictions/{pid}",
            headers=HEADERS
        ).json()

        if res["status"] == "succeeded":
            return res["output"][0]

        if res["status"] == "failed":
            raise Exception("Generation failed")

        time.sleep(2)


@bot.message_handler(content_types=["photo"])
def handle_photo(message):
    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

    bot.send_message(message.chat.id, "🧠 Генерирую Nano-Banana стиль...")

    try:
        img_url = generate_image(file_url)
        bot.send_photo(message.chat.id, img_url)
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка генерации: {e}")


bot.infinity_polling()
