import os, requests, telebot, datetime, pytz, re
from flask import Flask, request
from telebot import types

# --- [ AMBIL DATA VARIABEL ] ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY") 
MY_USER_ID = int(os.getenv("MY_USER_ID", "8227188993"))
PORT = int(os.environ.get("PORT", 8080))

# JALUR SUPER STABIL (v1beta dengan penamaan model lengkap)
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_KEY}"

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)
app = Flask(__name__)

def get_waktu():
    return datetime.datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%d/%m/%Y %H:%M:%S")

def tombol_movie():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎬 Join Channel @SheJua", url="https://t.me/SheJua"))
    return markup

# --- [ OTAK JONI ] ---
def get_response(text, name):
    prompt = (
        f"Kamu Joni, pakar film manusia asli @SheJua. JANGAN SEBUT BOT/AI. "
        f"Jawab santai, asik, pakai emoji film. Sapa Kak {name}. "
        f"Waktu: {get_waktu()}. Pertanyaan: {text}"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        # Panggil Google dengan timeout lebih lama agar gesit
        res = requests.post(GEMINI_URL, json=payload, timeout=25)
        data = res.json()
        
        if 'candidates' in data and data['candidates']:
            return data['candidates'][0]['content']['parts'][0]['text']
        else:
            # Jika masih error, Joni beri tahu Admin lewat log
            print(f"🚨 DEBUG GOOGLE: {data}")
            return f"Aduh Kak {name}, otak Joni lagi pening di pusat Google. Coba tanya judul film lain ya! 🍿"
    except Exception as e:
        print(f"🚨 DEBUG SYSTEM: {e}")
        return "Sori sob, koneksi otak Joni lagi keganggu. 🙏"

@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def receive_update():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def index():
    return "Joni @SheJua is Alive! 🚀", 200

# --- [ HANDLER CHAT ] ---
@bot.message_handler(func=lambda m: m.text and not m.text.startswith("/"))
def chat_handler(m):
    f_name = m.from_user.first_name
    u_id = m.from_user.id
    text_low = m.text.lower()
    
    # 1. LOGIKA PRIVATE CHAT (Pintu Rahasia Kakak)
    if m.chat.type == 'private':
        if u_id == MY_USER_ID:
            bot.send_chat_action(m.chat.id, 'typing')
            jawaban = get_response(m.text, f_name)
            bot.reply_to(m, f"🧪 **MODE TESTING ADMIN**\n━━━━━━━━━━━━━━━\n{jawaban}")
        else:
            teks_tolak = (
                f"Halo Kak {f_name}! 👋\n\n"
                f"Maaf ya, Joni cuma bertugas di grup **@SheJua**. "
                f"Silakan gabung grup untuk ngobrol atau hubungi admin @shejua ya! 🍿📽️"
            )
            bot.reply_to(m, teks_tolak, reply_markup=tombol_movie())
        return

    # 2. LOGIKA DI GRUP (Sapaan 'sob' atau Reply)
    is_me = m.reply_to_message and m.reply_to_message.from_user.id == bot.get_me().id
    if "sob" in text_low or is_me:
        bot.send_chat_action(m.chat.id, 'typing')
        jawaban = get_response(m.text, f_name)
        bot.reply_to(m, jawaban, reply_markup=tombol_movie())

# --- [ HANDLER REQUEST ] ---
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("#request"))
def handle_req(m):
    # Regex untuk ambil judul dan tahun (4 digit)
    match = re.search(r"#request\s+(.+)\s+(\d{4})", m.text, re.IGNORECASE)
    
    if match:
        judul, tahun = match.group(1).strip(), match.group(2).strip()
        konfirmasi = (
            f"✅ **REQUEST DITERIMA!**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🎬 **Film:** `{judul}`\n"
            f"📅 **Tahun:** `{tahun}`\n\n"
            f"Sabar ya Kak {m.from_user.first_name}, Joni sudah lapor ke Admin @SheJua! 🍿"
        )
        bot.reply_to(m, konfirmasi, parse_mode="Markdown")
        
        # Lapor ke Saved Message Kakak
        bot.send_message(MY_USER_ID, f"🚨 **NEW REQ**\n👤: {m.from_user.first_name}\n🎬: {judul} ({tahun})\n⏰: {get_waktu()}")
    else:
        # Respon jika tidak ada tahun
        teks_salah = (
            f"❌ **FORMAT SALAH, KAK!**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"Joni butuh tahunnya biar nggak ketukar filmnya. 🙏\n\n"
            f"👉 Contoh: `#request Joker 2024`"
        )
        bot.reply_to(m, teks_salah, parse_mode="Markdown")

if __name__ == "__main__":
    # Kirim tanda "Lapor Bangun" ke Admin
    try:
        bot.send_message(MY_USER_ID, "📍 **Upload Complete Selamat Menyaksikan**\nJoni sudah bangun dan siap melayani Kakak! 🚀")
    except: pass
    app.run(host="0.0.0.0", port=PORT)
