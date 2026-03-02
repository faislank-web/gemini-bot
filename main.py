import os, requests, telebot, datetime, pytz, re, random
from flask import Flask, request
from telebot import types

# --- [ KONFIGURASI ] ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY") 
MY_USER_ID = int(os.getenv("MY_USER_ID", "8227188993"))
PORT = int(os.environ.get("PORT", 8080))

# JALUR SUPER STABIL 2026 (v1beta dengan model flash-latest)
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_KEY}"

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)
app = Flask(__name__)

def get_waktu():
    return datetime.datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%H:%M:%S")

# --- [ VARIASI ALASAN MANUSIAWI ] ---
def get_excuse(name):
    pilihan = [
        f"Waduh Kak {name}, Joni lagi sibuk sortir film terbaru di storage nih. Coba tanya judul lain ya! 🍿",
        f"Sori sob, Joni lagi rekap database film buat minggu depan. Bentar lagi ya! 🎬",
        f"Aduh, sinyal di bioskop lagi bapuk banget nih Kak {name}. Coba lagi bentar ya! 📽️",
        f"Joni lagi maraton cek kualitas video nih sob, otaknya agak panas dikit. Coba lagi ya! 🎞️"
    ]
    return random.choice(pilihan)

# --- [ OTAK JONI ] ---
def get_response(text, name):
    prompt = (
        f"Kamu Joni, manusia asli pakar film di @SheJua. JANGAN SEBUT AI/BOT/GOOGLE. "
        f"Gaya bahasa: Santai, asik, teman nongkrong. Sapa Kak {name}. "
        f"Sekarang jam {get_waktu()}. Jawab pertanyaan ini: {text}"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(GEMINI_URL, json=payload, timeout=25)
        data = res.json()
        if 'candidates' in data and data['candidates']:
            return data['candidates'][0]['content']['parts'][0]['text']
        else:
            print(f"🚨 GOOGLE LOG: {data}")
            return get_excuse(name)
    except:
        return f"Sori Kak {name}, Joni lagi pening dikit habis maraton film. Coba lagi nanti ya! 🙏"

@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def receive_update():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def index():
    try:
        bot.send_message(MY_USER_ID, "📍 **Upload Complete Selamat Menyaksikan**\nJoni sudah bangun dan siap melayani Kakak! 🚀")
    except: pass
    return "Joni @SheJua is Online! 🚀", 200

# --- [ HANDLER ADMIN & TESTING ] ---
@bot.message_handler(func=lambda m: m.chat.type == 'private')
def private_handler(m):
    f_name = m.from_user.first_name
    if m.from_user.id == MY_USER_ID:
        bot.send_chat_action(m.chat.id, 'typing')
        jawaban = get_response(m.text, f_name)
        bot.reply_to(m, f"🧪 **DATA SIAP DIUJI (ADMIN ONLY)**\n━━━━━━━━━━━━━━━\n{jawaban}")
    else:
        bot.reply_to(m, f"Maaf Kak {f_name}, Joni cuma tugas di grup @SheJua ya! ✨")

# --- [ HANDLER #REQUEST ] ---
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("#request"))
def handle_req(m):
    match = re.search(r"#request\s+(.+)\s+(\d{4})", m.text, re.IGNORECASE)
    if match:
        judul, tahun = match.group(1).strip(), match.group(2).strip()
        bot.reply_to(m, f"✅ **Request Diterima!**\n\nFilm **{judul} ({tahun})** sudah Joni catat buat Admin @SheJua! 🍿")
        bot.send_message(MY_USER_ID, f"🚨 **NEW REQ**\n👤: {m.from_user.first_name}\n🎬: {judul} ({tahun})")
    else:
        bot.reply_to(m, "❌ **FORMAT SALAH!** Contoh: `#request Avatar 2022` 🎬")

# --- [ CHAT GRUP ] ---
@bot.message_handler(func=lambda m: m.text and not m.text.startswith("/"))
def group_chat(m):
    if "sob" in m.text.lower() or (m.reply_to_message and m.reply_to_message.from_user.id == bot.get_me().id):
        bot.send_chat_action(m.chat.id, 'typing')
        jawaban = get_response(m.text, m.from_user.first_name)
        bot.reply_to(m, jawaban)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
