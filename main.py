import os
import requests
import telebot
import datetime
import pytz
import re
from flask import Flask, request
from telebot import types

# --- [ AMBIL DATA DARI VARIABEL ZEABUR ] ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY") 
MY_USER_ID = int(os.getenv("MY_USER_ID", "8227188993"))
# Gunakan Port 8080 sebagai default sesuai log Zeabur Kakak
PORT = int(os.environ.get("PORT", 8080))

# URL API Gemini (Stabil Maret 2026)
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"

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

def get_gemini_response(user_text, first_name, username):
    waktu_skrg = get_waktu_jakarta()
    # Identitas Joni (Pakar Film Manusia, Bukan Bot)
    SYS_PROMPT = (
        f"Kamu adalah Joni, pakar film manusia asli dari Channel @SheJua. "
        f"Waktu: {waktu_skrg}. User: Kak {first_name} (@{username}). "
        f"Gayamu santai, asik, informatif soal film. JANGAN SEBUT KAMU AI/BOT."
    )
    
    payload = {"contents": [{"parts": [{"text": f"{SYS_PROMPT}\n\nPertanyaan: {user_text}"}]}]}
    
    try:
        res = requests.post(GEMINI_URL, json=payload, timeout=25)
        res_json = res.json()
        
        # Validasi respon agar tidak error 'candidates'
        if 'candidates' in res_json and res_json['candidates']:
            return res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            print(f"🚨 API Log: {res_json}")
            return f"Aduh Kak {first_name}, Google Studio Joni lagi ada kendala teknis (Warning). Tapi Joni tetep standby kok! Coba tanya judul film lain ya! 🍿"
            
    except Exception as e:
        print(f"🚨 System Error: {e}")
        return "Sori sob, sinyal otak Joni lagi keganggu. Coba lagi bentar ya! 🙏"

# --- [ ROUTE WEBHOOK ] ---
@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook_status():
    return f"Joni @SheJua is Online on Port {PORT}!", 200

# --- [ WELCOME MESSAGE ] ---
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new(m):
    for user in m.new_chat_members:
        bot.reply_to(m, f"Halo Kak {user.first_name}! 👋 Welcome di @SheJua!\n\nKetik rules request:\n👉 `#request [Judul] [Tahun]`\nContoh: `#request Joker 2024`", reply_markup=movie_buttons())

# --- [ HANDLER CHAT & REQUEST ] ---
@bot.message_handler(func=lambda m: True)
def chat_handler(m):
    if not m.text: return
    
    f_name = m.from_user.first_name
    u_name = m.from_user.username if m.from_user.username else "User"
    text = m.text.strip()

    # Blokir Private Chat
    if m.chat.type == 'private':
        bot.reply_to(m, "Joni cuma tugas di grup @SheJua ya Kak! Hubungi @shejua untuk bantuan.", reply_markup=movie_buttons())
        return

    # Logika Request Film
    if text.lower().startswith("#request"):
        match = re.search(r"#request\s+(.+)\s+(\d{4})", text, re.IGNORECASE)
        if match:
            judul, tahun = match.group(1).strip(), match.group(2).strip()
            bot.reply_to(m, f"Siapp sob! Request **{judul} ({tahun})** sudah diteruskan ke Admin @SheJua! 🎬")
            bot.send_message(MY_USER_ID, f"🚨 **NEW REQUEST**\n👤: {f_name} (@{u_name})\n🎬: {judul}\n📅: {tahun}")
        else:
            bot.reply_to(m, "Format salah sob! Wajib pakai tahun ya. Contoh: `#request Avatar 2022`")
        return

    # Trigger Respon Joni (sob, tag, atau reply)
    is_sob = "sob" in text.lower()
    is_tag = f"@{BOT_INFO.username.lower()}" in text.lower()
    is_reply = m.reply_to_message and m.reply_to_message.from_user.id == BOT_INFO.id

    if is_sob or is_tag or is_reply:
        bot.send_chat_action(m.chat.id, 'typing')
        ans = get_gemini_response(text, f_name, u_name)
        bot.reply_to(m, ans, reply_markup=movie_buttons())

# --- [ RUN SERVER ] ---
if __name__ == "__main__":
    # Pakai host 0.0.0.0 agar bisa diakses public oleh Zeabur
    app.run(host="0.0.0.0", port=PORT)
