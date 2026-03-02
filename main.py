import os
import requests
import telebot
import datetime
import pytz
import re
from flask import Flask, request
from telebot import types

# --- [ KONEKSI KE VARIABEL ZEABUR ] ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY") # Sesuaikan dengan nama di gambar Kakak
MY_USER_ID = int(os.getenv("MY_USER_ID", 8227188993))
ZEABUR_URL = os.getenv("ZEABUR_WEB_URL")

# API KONFIGURASI
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={GEMINI_KEY}"

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)
app = Flask(__name__)
BOT_INFO = bot.get_me()

def get_waktu_jakarta():
    tz = pytz.timezone('Asia/Jakarta')
    return datetime.datetime.now(tz).strftime("%A, %d %B %Y - %H:%M:%S")

def movie_buttons():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎬 Gabung Channel @SheJua", url="https://t.me/SheJua"),
        types.InlineKeyboardButton("☎️ Hubungi Admin", url="https://t.me/shejua")
    )
    return markup

def get_gemini_response(user_text, first_name, username, user_id):
    waktu_skrg = get_waktu_jakarta()
    SYS_PROMPT = (
        f"Kamu adalah Joni, pakar film manusia asli @SheJua. JANGAN BILANG KAMU BOT. "
        f"Waktu: {waktu_skrg}. Tahun 2026. User: Kak {first_name} (@{username}). "
        f"Jawab santai sebagai teman nongkrong di grup jika dipanggil 'sob' atau reply."
    )
    payload = {"contents": [{"parts": [{"text": f"{SYS_PROMPT}\n\nUser nanya: {user_text}"}]}]}
    try:
        res = requests.post(GEMINI_URL, json=payload, timeout=25)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except: return "Aduh sob, Joni lagi pening. Coba lagi ya! 🙏"

# --- [ HANDLER ANGGOTA BARU ] ---
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new(m):
    for user in m.new_chat_members:
        teks = (
            f"Halo Kak {user.first_name}! 👋 Selamat datang di @SheJua!\n\n"
            f"Ketik rules request ini ya:\n"
            f"👉 `#request [Judul Film] [Tahun]`\n\n"
            f"Contoh: `#request Joker 2024`"
        )
        bot.reply_to(m, teks, reply_markup=movie_buttons())

# --- [ WEBHOOK ROUTE ] ---
@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    return f"Joni @SheJua is Online at {ZEABUR_URL}", 200

# --- [ MAIN HANDLER CHAT & REQUEST ] ---
@bot.message_handler(func=lambda m: True)
def chat_handler(m):
    if not m.text: return
    
    f_name = m.from_user.first_name
    u_name = m.from_user.username if m.from_user.username else "User"
    u_id = m.from_user.id
    text = m.text.strip()

    # 1. PROTEKSI PRIVATE CHAT
    if m.chat.type == 'private':
        bot.reply_to(m, f"Maaf Kak {f_name}, Joni cuma kerja di grup @SheJua. Hubungi admin @shejua ya!", reply_markup=movie_buttons())
        return

    # 2. LOGIKA #REQUEST
    if text.lower().startswith("#request"):
        match = re.search(r"#request\s+(.+)\s+(\d{4})", text, re.IGNORECASE)
        if match:
            judul, tahun = match.group(1).strip(), match.group(2).strip()
            bot.reply_to(m, f"Siapp sob! Request **{judul} ({tahun})** dikirim ke Admin. 🎬")
            bot.send_message(MY_USER_ID, f"🚨 **NEW REQUEST**\n👤: {f_name} (@{u_name})\n🎬: {judul}\n📅: {tahun}")
        else:
            bot.reply_to(m, "Format salah sob! Wajib pakai tahun. Contoh: `#request Joker 2024`")
        return

    # 3. LOGIKA GEMINI
    text_lower = text.lower()
    if "sob" in text_lower or f"@{BOT_INFO.username.lower()}" in text_lower or (m.reply_to_message and m.reply_to_message.from_user.id == BOT_INFO.id):
        bot.send_chat_action(m.chat.id, 'typing')
        clean_text = text.replace(f"@{BOT_INFO.username}", "").replace("sob", "").replace("Sob", "").strip()
        ans = get_gemini_response(clean_text, f_name, u_name, u_id)
        bot.reply_to(m, ans, reply_markup=movie_buttons())

if __name__ == "__main__":
    # Menggunakan PORT otomatis dari Zeabur
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)
