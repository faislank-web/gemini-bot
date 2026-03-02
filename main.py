import os
import requests
import telebot
import datetime
import pytz
import re
from flask import Flask, request
from telebot import types

# --- [ AMBIL DATA DARI VARIABEL ZEABUR ] ---
# Pastikan nama di os.getenv SAMA PERSIS dengan di dashboard Zeabur Kakak
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY") 
TMDB_KEY = os.getenv("TMDB_KEY")
MY_USER_ID = int(os.getenv("MY_USER_ID", 8227188993))

# URL API Gemini (Stabil 2026)
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
    # Prompt Rahasia Joni (JANGAN BILANG BOT)
    SYS_PROMPT = (
        f"Kamu adalah Joni, pakar film manusia asli dari Channel @SheJua. "
        f"Waktu sekarang: {waktu_skrg}. User: Kak {first_name} (@{username}). "
        f"Gayamu santai, asik, pakai bahasa teman nongkrong. "
        f"Jika ditanya film, jawab dengan wawasan luas. "
        f"PENTING: JANGAN PERNAH SEBUT KAMU AI ATAU BOT."
    )
    
    payload = {
        "contents": [{
            "parts": [{"text": f"{SYS_PROMPT}\n\nPertanyaan User: {user_text}"}]
        }]
    }
    
    try:
        res = requests.post(GEMINI_URL, json=payload, timeout=30)
        res_json = res.json()
        # Ambil teks jawaban dari struktur JSON Gemini
        return res_json['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"Error Gemini: {e}")
        return "Aduh sob, Joni lagi agak pening nih koneksinya. Coba tanya lagi bentar ya! 🙏"

# --- [ WEBHOOK ROUTE ] ---
@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    return "Joni @SheJua is Online & Ready!", 200

# --- [ SAMBUT ANGGOTA BARU ] ---
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new(m):
    for user in m.new_chat_members:
        name = user.first_name
        teks = (
            f"Halo Kak {name}! 👋 Selamat datang di grup @SheJua!\n\n"
            f"Mau cari film? Pakai format request ini ya:\n"
            f"👉 `#request [Judul Film] [Tahun]`\n\n"
            f"Contoh: `#request Joker 2024`\n"
            f"Wajib pakai tahun biar Joni gampang nyarinya! 😊"
        )
        bot.reply_to(m, teks, reply_markup=movie_buttons())

# --- [ HANDLER UTAMA CHAT ] ---
@bot.message_handler(func=lambda m: True)
def chat_handler(m):
    if not m.text: return
    
    f_name = m.from_user.first_name
    u_name = m.from_user.username if m.from_user.username else "User"
    text = m.text.strip()
    text_lower = text.lower()

    # 1. TOLAK PRIVATE CHAT
    if m.chat.type == 'private':
        pesan_tolak = (
            f"Maaf ya Kak {f_name}, Joni nggak melayani chat pribadi. 🙏\n\n"
            f"Joni cuma kerja di dalam **Channel @SheJua**.\n"
            f"Silakan hubungi admin **@shejua** ya Kak! ✨"
        )
        bot.reply_to(m, pesan_tolak, reply_markup=movie_buttons())
        return

    # 2. LOGIKA VALIDASI #REQUEST
    if text_lower.startswith("#request"):
        # Cari judul dan tahun (4 digit angka)
        match = re.search(r"#request\s+(.+)\s+(\d{4})", text, re.IGNORECASE)
        
        if match:
            judul = match.group(1).strip()
            tahun = match.group(2).strip()
            
            # Balas ke Grup
            bot.reply_to(m, f"Siapp sob! Request film **{judul} ({tahun})** sudah Joni catat dan lapor ke Admin. Mohon ditunggu ya! 🎬🍿")
            
            # Kirim ke Pesan Tersimpan Kakak
            pesan_admin = (
                f"🚨 **NEW REQUEST FILM** 🚨\n"
                f"👤 Dari: {f_name} (@{u_name})\n"
                f"🎬 Judul: {judul}\n"
                f"📅 Tahun: {tahun}\n"
                f"⏰ Jam: {get_waktu_jakarta()}"
            )
            bot.send_message(MY_USER_ID, pesan_admin)
        else:
            bot.reply_to(m, f"Waduh Kak {f_name}, formatnya kurang lengkap. 😅\n\nWajib ada tahunnya! Contoh:\n`#request Avatar 2022`", parse_mode="Markdown")
        return

    # 3. RESPON AI (SOB / TAG / REPLY)
    is_sob = "sob" in text_lower
    is_tag = f"@{BOT_INFO.username.lower()}" in text_lower
    is_reply = m.reply_to_message and m.reply_to_message.from_user.id == BOT_INFO.id

    if is_sob or is_tag or is_reply:
        bot.send_chat_action(m.chat.id, 'typing')
        # Bersihkan teks dari tag bot
        clean_text = text.replace(f"@{BOT_INFO.username}", "").strip()
        
        ans = get_gemini_response(clean_text, f_name, u_name)
        bot.reply_to(m, ans, reply_markup=movie_buttons())

# --- [ JALANKAN SERVER ] ---
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)
