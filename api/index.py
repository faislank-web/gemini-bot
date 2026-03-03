import os, requests, telebot
from flask import Flask, request

# --- [ KONFIGURASI AMAN VERCEL ] ---
# Ambil dari Environment Variables (Settings > Environment Variables di Vercel)
TOKEN = os.getenv("TELEGRAM_TOKEN")
G_KEY = os.getenv("GEMINI_API_KEY")

# Menggunakan Jalur Gemini 2.5 Flash (Terbukti Sukses di CMD)
G_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={G_KEY}"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- [ FUNGSI OTAK JONI ] ---
def joni_brain(text, name):
    prompt = (
        f"Kamu Joni, manusia asli pakar film di grup @SheJua. JANGAN SEBUT DIRIMU AI/BOT. "
        f"Gunakan gaya bahasa santai, asik, dan akrab. Sapa Kak {name}. "
        f"Jawab pertanyaan ini dengan cerdas: {text}"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        # Request ke Google Gemini 2.5 Flash
        res = requests.post(G_URL, json=payload, timeout=25)
        data = res.json()
        # Mengambil hasil teks dari struktur JSON Gemini
        return data['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"Aduh sob {name}, Joni lagi pening dikit habis maraton film. Coba lagi ya! 🍿"

# --- [ ROUTE UTAMA VERCEL ] ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            update = telebot.types.Update.de_json(request.get_json(force=True))
            bot.process_new_updates([update])
            return "OK", 200
        except:
            return "Error", 500
    return "Joni @SheJua (Gemini 2.5 Flash) is Online! 🚀", 200

# --- [ FITUR COMMAND /IMDB ] ---
@bot.message_handler(commands=['imdb'])
def imdb_info(m):
    query = m.text.replace('/imdb', '').strip()
    if not query:
        bot.reply_to(m, "Kasih judul filmnya dong sob! Contoh: `/imdb Inception`")
        return
    bot.send_chat_action(m.chat.id, 'typing')
    jawaban = joni_brain(f"Berikan info lengkap IMDB (rating, tahun, sinopsis) untuk film: {query}", m.from_user.first_name)
    bot.reply_to(m, jawaban)

# --- [ FITUR CHAT OTOMATIS & REPLIES ] ---
@bot.message_handler(func=lambda m: True)
def group_chat(m):
    # Cek apakah ada kata "sob", reply ke bot, atau chat pribadi (PM)
    is_sob = m.text and "sob" in m.text.lower()
    is_reply = m.reply_to_message and m.reply_to_message.from_user.id == bot.get_me().id
    is_private = m.chat.type == 'private'

    if is_sob or is_reply or is_private:
        bot.send_chat_action(m.chat.id, 'typing')
        jawaban = joni_brain(m.text, m.from_user.first_name)
        bot.reply_to(m, jawaban)

# --- [ HANDLER UNTUK VERCEL SERVERLESS ] ---
def handler(request):
    return app(request)
