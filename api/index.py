import os, requests, telebot
from flask import Flask, request

# --- [ KONFIGURASI ] ---
# Pastikan nama variabel di Vercel Settings adalah MY_USER_ID
TOKEN = os.getenv("TELEGRAM_TOKEN")
G_KEY = os.getenv("GEMINI_API_KEY")
ADMIN = os.getenv("MY_USER_ID")
G_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={G_KEY}"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- [ FUNGSI OTAK JONI ] ---
def joni_brain(text, name):
    prompt = (
        f"Kamu Joni, manusia asli pakar film di grup @SheJua. JANGAN SEBUT DIRIMU AI/BOT. "
        f"Gunakan gaya bahasa santai dan asik. Sapa Kak {name}. "
        f"Pertanyaan: {text}"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(G_URL, json=payload, timeout=15)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"Aduh sob {name}, Joni lagi pening dikit (Log: {str(e)[:15]}). Coba lagi ya! 🍿"

# --- [ ROUTE UTAMA VERCEL ] ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            # Menggunakan get_data untuk stabilitas di Vercel
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return "OK", 200
        except Exception as e:
            print(f"Update Error: {e}")
            return "Error", 500
    return "Joni @SheJua is Online! 🚀", 200

# --- [ FITUR COMMANDS ] ---
@bot.message_handler(commands=['imdb'])
def imdb_info(m):
    query = m.text.replace('/imdb', '').strip()
    if not query:
        bot.reply_to(m, "Kasih judul filmnya dong sob! Contoh: `/imdb Inception`")
        return
    bot.send_chat_action(m.chat.id, 'typing')
    jawaban = joni_brain(f"Berikan info detail IMDB (rating, sinopsis, tahun) untuk film: {query}", m.from_user.first_name)
    bot.reply_to(m, jawaban)

# --- [ FITUR CHAT OTOMATIS ] ---
@bot.message_handler(func=lambda m: True)
def group_chat(m):
    # Logika nyaut: Private (Admin), Kata 'sob', atau Reply ke bot
    is_admin = m.chat.type == 'private' and str(m.from_user.id) == str(ADMIN)
    is_sob = m.text and "sob" in m.text.lower()
    is_reply = m.reply_to_message and m.reply_to_message.from_user.id == bot.get_me().id

    if is_admin or is_sob or is_reply:
        bot.send_chat_action(m.chat.id, 'typing')
        jawaban = joni_brain(m.text, m.from_user.first_name)
        bot.reply_to(m, jawaban)

# --- [ PINTU MASUK VERCEL ] ---
# Fungsi ini wajib ada agar Vercel tidak Error 500
def handler(request):
    return app(request)
