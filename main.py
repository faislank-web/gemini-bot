import os
import sys
import requests
import telebot
from telebot import types
import google.generativeai as genai
from flask import Flask, request

# --- [ DATA AKSES ] ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
ZEABUR_URL = os.environ.get("ZEABUR_WEB_URL")

# Inisialisasi AI
genai.configure(api_key=GEMINI_KEY)
instruction = (
    "Kamu adalah pakar film profesional dengan data IMDB lengkap. "
    "Jangan pernah awali jawaban dengan kata 'Halo'. "
    "Selalu panggil 'sob' di akhir kalimat dan bersikap cerdas."
)
model_ai = genai.GenerativeModel('gemini-1.5-flash', system_instruction=instruction)

# Memory Chat tiap user
user_sessions = {}

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# --- [ FUNGSI TOMBOL ADMIN ] ---
def admin_button():
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("Hubungi Admin", url="https://t.me/filmberbobot")
    markup.add(btn)
    return markup

def get_user_name_from_obj(user_obj):
    name = user_obj.first_name
    return name if name else user_obj.username

# --- [ HANDLER: MEMBER BARU MASUK ] ---
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    bot_id = bot.get_me().id
    for member in message.new_chat_members:
        # Jangan menyapa diri sendiri (bot)
        if member.id == bot_id:
            continue
        
        user_name = get_user_name_from_obj(member)
        welcome_text = (
            f"Kak {user_name}, selamat datang di grup sob!\n\n"
            "Saya adalah pakar film di sini. Kalau butuh info rating atau rekomendasi film IMDB, "
            "silakan reply pesan saya dan tambahkan kata 'sob' ya!"
        )
        bot.send_message(message.chat.id, welcome_text, reply_markup=admin_button())

# --- [ HANDLER: /IMDB ] ---
@bot.message_handler(commands=['imdb'])
def search_imdb(message):
    user_name = get_user_name_from_obj(message.from_user)
    query = message.text.split(' ', 1)[1] if len(message.text.split(' ')) > 1 else None
    
    if not query:
        bot.reply_to(message, f"Kak {user_name}, mau cari film apa sob? Contoh: /imdb Batman", reply_markup=admin_button())
        return
    
    prompt = f"Berikan daftar 3-5 judul film yang mirip dengan '{query}' lengkap dengan rating IMDB."
    try:
        response = model_ai.generate_content(prompt)
        text = f"🎬 **Kak {user_name}, ini hasil pencarian IMDB untuk '{query}':**\n\n{response.text}"
        bot.reply_to(message, text, reply_markup=admin_button())
    except:
        bot.reply_to(message, f"Database film lagi penuh nih Kak {user_name}, coba lagi nanti ya sob!", reply_markup=admin_button())

# --- [ HANDLER: CHAT AI (Reply + 'Sob') ] ---
@bot.message_handler(func=lambda m: True)
def ai_chat(message):
    teks = message.text.lower() if message.text else ""
    user_id = message.from_user.id
    user_name = get_user_name_from_obj(message.from_user)
    
    # Syarat: Harus ada kata 'sob' DAN membalas pesan bot
    if "sob" in teks and message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id:
        try:
            if user_id not in user_sessions:
                user_sessions[user_id] = model_ai.start_chat(history=[])
            
            chat_session = user_sessions[user_id]
            response = chat_session.send_message(message.text)
            
            final_text = f"Kak {user_name}, {response.text}"
            bot.reply_to(message, final_text, reply_markup=admin_button())
        except:
            bot.reply_to(message, f"Aduh Kak {user_name}, otak saya lagi ngebul nih sob!", reply_markup=admin_button())

# --- [ WEBHOOK SETUP ] ---
@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def get_message():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    return "Forbidden", 403

@app.route('/')
def setup():
    if not ZEABUR_URL: return "Set ZEABUR_WEB_URL!", 500
    clean_url = ZEABUR_URL.replace("https://", "").replace("http://", "").strip("/")
    bot.remove_webhook()
    bot.set_webhook(url=f"https://{clean_url}/{TELEGRAM_TOKEN}")
    return "<h1>📍 Upload Complete Selamat Menyaksikan</h1>", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
