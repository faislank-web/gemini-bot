import os
import requests
import telebot
import datetime
import pytz
import re
from flask import Flask, request
from telebot import types

# --- [ DATA AKSES KAKAK - UPDATE ID 2026 ] ---
TELEGRAM_TOKEN = "8485819414:AAFuMaapg-DJ6s5FpNjRPFUU6gAr9Cv18aw"
GEMINI_KEY = "AIzaSyDk9JZFNXTAeZW5pqRs2sOnwmONUtsG5FM" 
TMDB_KEY = "61e2290429798c561450eb56b26de19b"
MY_USER_ID = 8227188993  # ID Baru Kakak untuk terima Request

# MODEL TERBARU KAKAK: Gemini 3 Flash Preview
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
    except: return "Duh sob, Joni lagi pening. Coba lagi ya! 🙏"

# --- [ HANDLER ANGGOTA BARU ] ---
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new(m):
    for user in m.new_chat_members:
        name = user.first_name
        teks = (
            f"Halo Kak {name}! 👋 Selamat datang di grup @SheJua!\n\n"
            f"Biar Joni gampang cariin filmnya, silakan ketik rules request ini:\n"
            f"👉 `#request [Judul Film] [Tahun]`\n\n"
            f"Contoh: `#request Joker 2024`\n"
            f"Jangan lupa tahunnya ya biar Joni nggak linglung! 😊"
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
    return "Joni @SheJua 2026 is Active!", 200

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
        bot.reply_to(m, f"Maaf ya Kak {f_name}, Joni cuma kerja di grup @SheJua. Hubungi admin @shejua ya! ✨", reply_markup=movie_buttons())
        return

    # 2. LOGIKA #REQUEST (CEK JUDUL & TAHUN)
    if text.lower().startswith("#request"):
        # Regex untuk mencari #request [judul] [4 digit angka tahun]
        match = re.search(r"#request\s+(.+)\s+(\d{4})", text, re.IGNORECASE)
        
        if match:
            judul = match.group(1).strip()
            tahun = match.group(2).strip()
            
            # Balasan ke grup
            bot.reply_to(m, f"Siapp sob! Request film **{judul} ({tahun})** sudah Joni kirim ke Admin. Mohon ditunggu ya! 🎬🍿")
            
            # TERUSKAN KE ID KAKAK (SAVED MESSAGES)
            pesan_admin = (
                f"🚨 **NEW REQUEST FILM** 🚨\n"
                f"--------------------------\n"
                f"👤 Dari: Kak {f_name} (@{u_name})\n"
                f"🆔 User ID: {u_id}\n"
                f"🎬 Judul: {judul}\n"
                f"📅 Tahun: {tahun}\n"
                f"⏰ Waktu: {get_waktu_jakarta()}\n"
                f"--------------------------"
            )
            bot.send_message(MY_USER_ID, pesan_admin)
        else:
            # Jika format salah (tanpa tahun atau salah tulis)
            bot.reply_to(m, f"Waduh Kak {f_name}, format request-nya kurang lengkap tuh. 😅\n\nWajib pakai tahun ya! Contoh:\n`#request Spiderman 2024`", parse_mode="Markdown")
        return

    # 3. LOGIKA GEMINI (SOB, TAG, REPLY)
    text_lower = text.lower()
    is_sob = "sob" in text_lower
    is_tag = f"@{BOT_INFO.username.lower()}" in text_lower
    is_reply = m.reply_to_message and m.reply_to_message.from_user.id == BOT_INFO.id

    if is_sob or is_tag or is_reply:
        bot.send_chat_action(m.chat.id, 'typing')
        clean_text = text.replace(f"@{BOT_INFO.username}", "").replace("sob", "").replace("Sob", "").strip()
        ans = get_gemini_response(clean_text, f_name, u_name, u_id)
        bot.reply_to(m, ans, reply_markup=movie_buttons())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
