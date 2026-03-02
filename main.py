import os, requests, telebot, datetime, pytz, re, random
from flask import Flask, request
from telebot import types

# --- [ AMBIL DATA VARIABEL ] ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY") 
MY_USER_ID = int(os.getenv("MY_USER_ID", "8227188993"))
PORT = int(os.environ.get("PORT", 8080))

# JALUR STABIL v1beta - Tanpa embel-embel '-latest' agar tidak 404
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_KEY}"

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)
app = Flask(__name__)

def get_waktu():
    return datetime.datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%d/%m/%Y %H:%M:%S")

# --- [ VARIASI ALASAN MANUSIAWI ] ---
def get_excuse(name):
    pilihan = [
        f"Aduh Kak {name}, Joni lagi sibuk sortir film baru nih. Coba tanya judul lain dulu ya! 🍿",
        f"Sori sob, Joni lagi rekap database mingguan @SheJua. Sabar ya! 🎬",
        f"Duh, sinyal di bioskop lagi bapuk banget Kak {name}. Coba lagi bentar ya! 📽️",
        f"Joni lagi maraton cek kualitas video nih, otaknya agak panas dikit. Tanya lagi nanti ya! 🎞️"
    ]
    return random.choice(pilihan)

# --- [ OTAK JONI ] ---
def get_response(text, name):
    prompt = (
        f"Kamu Joni, manusia asli pakar film di @SheJua. JANGAN SEBUT AI/BOT/GOOGLE. "
        f"Sapa Kak {name}. Jawab santai sebagai teman nongkrong. "
        f"Sekarang jam {get_waktu()}. Pertanyaan: {text}"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(GEMINI_URL, json=payload, timeout=25)
        data = res.json()
        if 'candidates' in data and data['candidates']:
            return data['candidates'][0]['content']['parts'][0]['text']
        else:
            # Jika Google kirim error, kita pakai alasan manusiawi
            print(f"🚨 GOOGLE LOG: {data}")
            return get_excuse(name)
    except Exception as e:
        print(f"🚨 SYSTEM LOG: {e}")
        return f"Sori Kak {name}, Joni lagi pening dikit habis maraton film. Coba lagi nanti ya! 🙏"

@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def receive_update():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def index():
    return "Joni @SheJua is Online! 🚀", 200

# --- [ HANDLER CHAT PERSONAL (ADMIN ONLY) ] ---
@bot.message_handler(func=lambda m: m.chat.type == 'private')
def private_handler(m):
    f_name = m.from_user.first_name
    if m.from_user.id == MY_USER_ID:
        bot.send_chat_action(m.chat.id, 'typing')
        jawaban = get_response(m.text, f_name)
        bot.reply_to(m, f"🧪 **DATA SIAP DIUJI (ADMIN ONLY)**\n━━━━━━━━━━━━━━━\n{jawaban}")
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎬 Join @SheJua", url="https://t.me/SheJua"))
        bot.reply_to(m, f"Maaf Kak {f_name}, Joni cuma tugas di grup @SheJua ya! ✨", reply_markup=markup)

# --- [ HANDLER #REQUEST ] ---
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("#request"))
def handle_req(m):
    match = re.search(r"#request\s+(.+)\s+(\d{4})", m.text, re.IGNORECASE)
    if match:
        judul, tahun = match.group(1).strip(), match.group(2).strip()
        bot.reply_to(m, f"✅ **Request Diterima!**\n\nFilm **{judul} ({tahun})** sudah Joni catat buat Admin @SheJua! 🍿")
        bot.send_message(MY_USER_ID, f"🚨 **REQ BARU**\n👤: {m.from_user.first_name}\n🎬: {judul} ({tahun})\n⏰: {get_waktu()}")
    else:
        bot.reply_to(m, "❌ **FORMAT SALAH!**\n\nContoh: `#request Avatar 2022` 🎬")

# --- [ CHAT GRUP ] ---
@bot.message_handler(func=lambda m: m.text and not m.text.startswith("/"))
def group_chat(m):
    if "sob" in m.text.lower() or (m.reply_to_message and m.reply_to_message.from_user.id == bot.get_me().id):
        bot.send_chat_action(m.chat.id, 'typing')
        jawaban = get_response(m.text, m.from_user.first_name)
        bot.reply_to(m, jawaban)

if __name__ == "__main__":
    # Tanda Bangun (Langsung panggil di main agar pasti terkirim)
    try:
        bot.send_message(MY_USER_ID, "📍 **Upload Complete Selamat Menyaksikan**\nJoni sudah bangun dan siap melayani Kakak! 🚀")
    except Exception as e:
        print(f"❌ Gagal kirim pesan bangun: {e}")
    app.run(host="0.0.0.0", port=PORT)
