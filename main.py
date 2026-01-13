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
        "🍌 Nano-Banana\n\n"
        "1️⃣ Напиши, как изменить фото\n"
        "2️⃣ Потом отправь фото"
    )

@bot.message_handler(content_types=["text"])
def save_prompt(msg):
    user_prompt[msg.chat.id] = msg.text
    bot.send_message(msg.chat.id, "📸 Теперь отправь фото")

def upload_to_telegraph(img):
    r = requests.post("https://telegra.ph/upload", files={"file": ("img.jpg", img)})
    j = r.json()
    return "https://telegra.ph" + j[0]["src"]

@bot.message_handler(content_types=["photo"])
def handle(msg):
    try:
        prompt = user_prompt.get(msg.chat.id)
        if not prompt:
            bot.send_message(msg.chat.id, "Сначала напиши текст, потом фото.")
            return

        # download photo
        file_id = msg.photo[-1].file_id
        file_info = bot.get_file(file_id)
        img = requests.get(
            f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
        ).content

        # upload
        image_url = upload_to_telegraph(img)

        # send to Replicate
        payload = {
            "version": "lucataco/nano-banana",
            "input": {
                "image": image_url,
                "prompt": prompt
            }
        }

        r = requests.post("https://api.replicate.com/v1/predictions", json=payload, headers=headers)
        j = r.json()

        if "id" not in j:
            bot.send_message(msg.chat.id, f"❌ Replicate error:\n{j}")
            return

        pid = j["id"]

        # poll
        for _ in range(30):
            time.sleep(2)
            s = requests.get(
                f"https://api.replicate.com/v1/predictions/{pid}",
                headers=headers
            ).json()

            if not isinstance(s, dict):
                bot.send_message(msg.chat.id, "❌ Replicate returned invalid response")
                return

            if s["status"] == "succeeded":
                output = s["output"]

                if isinstance(output, list):
                    bot.send_photo(msg.chat.id, output[0])
                elif isinstance(output, str):
                    bot.send_photo(msg.chat.id, output)
                else:
                    bot.send_message(msg.chat.id, f"❌ Unexpected output: {output}")

                return

            if s["status"] == "failed":
                bot.send_message(msg.chat.id, f"❌ Generation failed:\n{s}")
                return

        bot.send_message(msg.chat.id, "❌ Timeout. Nano-Banana did not respond.")

    except Exception as e:
        bot.send_message(msg.chat.id, f"❌ Ошибка: {e}")

bot.infinity_polling(skip_pending=True)
