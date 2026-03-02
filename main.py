import os, requests, telebot, datetime, pytz, re
from flask import Flask, request

# --- [ AMBIL VARIABEL ZEABUR ] ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY") 
MY_USER_ID = int(os.getenv("MY_USER_ID", "8227188993"))
PORT = int(os.environ.get("PORT", 8080))

# JALUR BARU (PASTI KETEMU - VERSI v1)
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)
app = Flask(__name__)

def get_waktu():
    return datetime.datetime.now(pytz.timezone('Asia/Jakarta')).strftime("%H:%M:%S")

# --- [ OTAK JONI ] ---
def get_response(text, name):
    # Prompt agar Joni tetap manusiawi
    prompt = f"Kamu Joni, pakar film asik @SheJua. JANGAN SEBUT BOT/AI. Jawab santai sebagai teman nongkrong. User: {name}. Pertanyaan: {text}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        # Panggil Google
        res = requests.post(GEMINI_URL, json=payload, timeout=25)
        data = res.json()
        
        # Cek jika Google kasih jawaban
        if 'candidates' in data and data['candidates']:
            return data['candidates'][0]['content']['parts'][0]['text']
        else:
            # Log Error ke Zeabur biar kita bisa intip
            print(f"🚨 GOOGLE NGAMUK: {data}")
            return f"Aduh sob, otak Joni lagi agak error di pusat Google. Coba tanya judul film lain ya! 🍿"
            
    except Exception as e:
        print(f"🚨 SYSTEM ERROR: {e}")
        return "Sori sob, Joni lagi pening berat. Coba lagi bentar ya! 🙏"

# --- [ JALUR KOMUNIKASI ] ---
@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def receive_update():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def index():
    return "Joni @SheJua is Online!", 200

# --- [ FITUR /RULES ] ---
@bot.message_handler(commands=['rules', 'start'])
def rules(m):
    teks = (
        "🎬 **CARA PANGGIL JONI** 🎬\n\n"
        "1. Ketik kata **'sob'** dalam chatmu.\n"
        "2. Atau **Reply** (balas) pesan Joni langsung.\n"
        "3. Request film? Ketik: `#request Judul Tahun`\n\n"
        "Contoh: `sob, rekomendasi film horor dong!`"
    )
    bot.reply_to(m, teks, parse_mode="Markdown")

# --- [ FITUR #REQUEST ] ---
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("#request"))
def handle_req(m):
    # Pola: #request [Judul] [4 Digit Tahun]
    match = re.search(r"#request\s+(.+)\s+(\d{4})", m.text, re.IGNORECASE)
    if match:
        judul, tahun = match.group(1).strip(), match.group(2).strip()
        bot.reply_to(m, f"Siapp sob! Request **{judul} ({tahun})** sudah Joni catat dan lapor ke Admin! 🎬")
        
        # Lapor ke Saved Message Kakak
        bot.send_message(MY_USER_ID, f"🚨 **REQ BARU**\n👤: {m.from_user.first_name}\n🎬: {judul} ({tahun})\n⏰: {get_waktu()}")
    else:
        bot.reply_to(m, "Format salah sob! Contoh: `#request Joker 2024` (Wajib pakai tahun)")

# --- [ RESPON CHAT ] ---
@bot.message_handler(func=lambda m: m.text and not m.text.startswith("/"))
def chat(m):
    text_low = m.text.lower()
    # Cek apakah dipanggil 'sob' atau di-reply
    is_me = m.reply_to_message and m.reply_to_message.from_user.id == bot.get_me().id
    
    if "sob" in text_low or is_me:
        bot.send_chat_action(m.chat.id, 'typing')
        jawaban = get_response(m.text, m.from_user.first_name)
        bot.reply_to(m, jawaban)

if __name__ == "__main__":
    # Pakai Port Zeabur 8080
    app.run(host="0.0.0.0", port=PORT)
