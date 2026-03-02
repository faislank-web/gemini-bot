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
MY_USER_ID = int(os.getenv("MY_USER_ID", 8227188993))
TMDB_KEY = os.getenv("TMDB_KEY")

# URL API Gemini (Menggunakan v1beta untuk akses lebih luas)
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
    SYS_PROMPT = (
        f"Kamu adalah Joni, pakar film dari @SheJua. JANGAN SEBUT BOT/AI. "
        f"Waktu: {waktu_skrg}. User: Kak {first_name}. "
        f"Gaya bahasa: Santai, asik, teman nongkrong."
    )
    
    payload = {"contents": [{"parts": [{"text": f"{SYS_PROMPT}\n\nNanya: {user_text}"}]}]}
    
    try:
        res = requests.post(GEMINI_URL, json=payload, timeout=30)
        res_json = res.json()
        
        # Jika API Key Valid dan ada respon
        if 'candidates' in res_json and res_json['candidates']:
            return res_json['candidates'][0]['content']['parts'][0]['text']
        
        # Jika API Error (Warning di Google Studio)
        print(f"🚨 Detail Error Google: {res_json}")
        return (f"Aduh Kak {first_name}, kayaknya Google Studio Joni lagi ada 'Warning' nih di pusat. "
                "Tapi tenang sob, Joni tetep di sini! Coba tanya judul film lain atau langsung #request aja ya! 🍿")
                
    except Exception as e:
        print(f"🚨 System Error: {e}")
        return "Duh sob, kabel otak Joni lagi korslet bentar. Coba lagi ya! 🙏"

@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    return "Joni Online!", 200

@bot.message_handler(content_types=['new_chat_members'])
def welcome_new(m):
    for user in m.new_chat_members:
        bot.reply_to(m, f"Halo Kak {user.first_name}! 👋 Welcome di @SheJua!\n\nKetik rules request:\n👉 `#request [Judul] [Tahun]`", reply_markup=movie_buttons())

@bot.message_handler(func=lambda m: True)
def chat_handler(m):
    if not m.text: return
    
    f_name = m.from_user.first_name
    u_name = m.from_user.username if m.from_user.username else "User"
    text = m.text.strip()

    if m.chat.type == 'private':
        bot.reply_to(m, "Hubungi admin @shejua ya Kak!", reply_markup=movie_buttons())
        return

    if text.lower().startswith("#request"):
        match = re.search(r"#request\s+(.+)\s+(\d{4})", text, re.IGNORECASE)
        if match:
            judul, tahun = match.group(1).strip(), match.group(2).strip()
            bot.reply_to(m, f"Siapp sob! Request **{judul} ({tahun})** dikirim ke Admin! 🎬")
            bot.send_message(MY_USER_ID, f"🚨 **NEW REQUEST**\n👤: {f_name}\n🎬: {judul}\n📅: {tahun}")
        else:
            bot.reply_to(m, "Format salah sob! Contoh: `#request Joker 2024`")
        return

    # Trigger Joni (panggil sob, tag, atau reply)
    if "sob" in text.lower() or f"@{BOT_INFO.username.lower()}" in text.lower() or (m.reply_to_message and m.reply_to_message.from_user.id == BOT_INFO.id):
        bot.send_chat_action(m.chat.id, 'typing')
        ans = get_gemini_response(text, f_name, u_name)
        bot.reply_to(m, ans, reply_markup=movie_buttons())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
