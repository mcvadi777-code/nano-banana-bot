import telebot
import requests
import base64
import os

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
    bot.send_message(msg.chat.id, "🍌 Nano-Banana\n\nНапиши, как изменить фото, затем отправь его.")

@bot.message_handler(content_types=["text"])
def save_prompt(msg):
    user_prompt[msg.chat.id] = msg.text
    bot.send_message(msg.chat.id, "📸 Теперь отправь фото.")

@bot.message_handler(content_types=["photo"])
def handle_photo(msg):
    try:
        prompt = user_prompt.get(msg.chat.id)
        if not prompt:
            bot.send_message(msg.chat.id, "Сначала напиши, как изменить изображение.")
            return

        file_id = msg.photo[-1].file_id
        file_info = bot.get_file(file_id)
        img = requests.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}")

        img64 = base64.b64encode(img.content).decode()

        payload = {
            "version": "lucataco/nano-banana",
            "input": {
                "image": img64,
                "prompt": prompt
            }
        }

        r = requests.post("https://api.replicate.com/v1/predictions", json=payload, headers=headers)

        prediction = r.json()
        prediction_id = prediction["id"]

        # ждём пока сгенерируется
        while True:
            status = requests.get(
                f"https://api.replicate.com/v1/predictions/{prediction_id}",
                headers=headers
            ).json()

            if status["status"] == "succeeded":
                image_url = status["output"][0]
                img = requests.get(image_url).content
                bot.send_photo(msg.chat.id, img)
                return

            if status["status"] == "failed":
                bot.send_message(msg.chat.id, "❌ Generation failed")
                return

    except Exception as e:
        bot.send_message(msg.chat.id, f"❌ Ошибка: {e}")

bot.infinity_polling(skip_pending=True)
