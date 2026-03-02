import os
import requests
import telebot
from telebot import types
from google import genai
from flask import Flask, request

# --- [ DATA AKSES ] ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
ZEABUR_URL = os.environ.get("ZEABUR_WEB_URL")
TMDB_KEY = "61e2290429798c561450eb56b26de19b"

# --- [ KONFIGURASI ] ---
client = genai.Client(api_key=GEMINI_KEY)
# PERBAIKAN: Nama model langsung tanpa prefix apa pun
MODEL_LIST = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.0-flash']

SYS_INSTRUCT = (
    "Kamu adalah manusia bernama Joni, seorang pakar film yang asik. "
    "Jangan pernah bilang kamu AI atau bot. Bicaralah seperti teman akrab. "
    "Kalau ada yang tanya film, ceritakan sinopsis dan infonya dengan seru. "
    "Di chat personal, langsung jawab santai. Di grup, panggil 'sob' kalau di-reply."
)

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

def admin_button():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("☎️ Chat Admin", url="https://t.me/filmberbobot"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    nama = message.from_user.first_name
    teks = (
        f"Eh, Kak {nama}! 👋 Senang ketemu Kakak lagi.\n\n"
        f"Tanya-tanya soal film langsung ketik aja ya. "
        f"Atau mau pake /imdb [judul] biar lebih lengkap infonya.\n"
        f"Oiya, cek /rules dulu ya biar enak.\n\n"
        f"Selamat menyaksikan! 🎬"
    )
    bot.reply_to(message, teks, reply_markup=admin_button())

@bot.message_handler(commands=['rules'])
def send_rules(message):
    rules = (
        "📜 **ATURAN KITA**\n"
        "---------------------------\n"
        "1. Santai aja, jangan spam ya Kak.\n"
        "2. Cari info detail? Pake /imdb [judul].\n"
        "3. Mau request? Ketik: `#request Judul Tahun`.\n"
        "4. Tetap sopan biar makin akrab!\n"
        "---------------------------"
    )
    bot.reply_to(message, rules, parse_mode="Markdown")

@bot.message_handler(func=lambda m: "#request" in m.text.lower())
def handle_movie_request(message):
    text = message.text.lower().replace("#request", "").strip()
    words = text.split()
    nama = message.from_user.first_name

    if not text:
        bot.reply_to(message, f"Duh Kak {nama}, tulis judul sama tahunnya dong biar aku carinya gampang. Contoh: `#request Avatar 2022`.")
    elif len(words) < 2:
        bot.reply_to(message, f"Maaf ya Kak {nama}, tahunnya mana? Harus lengkap biar nggak salah film. Contoh: `#request {text} 2024`.")
    else:
        bot.reply_to(message, f"Sip, permintaan Kak {nama} sudah aku simpan ya! Ditunggu kabar baiknya.")
        # Simpan ke Saved Messages (ID pengirim)
        bot.forward_message(message.from_user.id, message.chat.id, message.message_id)

@bot.message_handler(func=lambda m: True)
def chat_ai(message):
    is_private = message.chat.type == 'private'
    is_reply = message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id

    if is_private or (is_reply and "sob" in message.text.lower()):
        response_text = None
        for model_name in MODEL_LIST:
            try:
                # PERBAIKAN: Cara panggil model yang benar untuk google-genai
                response = client.models.generate_content(
                    model=model_name,
                    contents=message.text,
                    config={'system_instruction': SYS_INSTRUCT}
                )
                response_text = response.text
                if response_text: break
            except Exception as e:
                print(f"Gagal pakai {model_name}: {e}")
                continue
        
        if response_text:
            bot.reply_to(message, f"Kak {message.from_user.first_name}, {response_text}", reply_markup=admin_button())
        else:
            bot.reply_to(message, "Aduh, kepalaku lagi pening banget Kak, bentar ya aku istirahat dulu. Coba lagi nanti!")

@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def get_message():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return "OK", 200

@app.route('/')
def setup():
    url = ZEABUR_URL.replace("https://", "").replace("http://", "").strip("/")
    bot.remove_webhook()
    bot.set_webhook(url=f"https://{url}/{TELEGRAM_TOKEN}")
    return "<h1>📍 Upload Complete Selamat Menyaksikan</h1>", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
