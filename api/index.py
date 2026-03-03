import os
import requests
import telebot
from flask import Flask, request

# --- [ AMBIL DATA DARI ENVIRONMENT ] ---
TOKEN = "8485819414:AAFuMaapg-DJ6s5FpNjRPFUU6gAr9Cv18aw"
G_KEY = "AIzaSyDk9JZFNXTAeZW5pqRs2sOnwmONUtsG5FM"
ADMIN = os.getenv("MY_USER_ID")
G_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={G_KEY}"

# Inisialisasi
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
    except:
        return f"Aduh sob {name}, Joni lagi pening dikit. Coba lagi ya! 🍿"

# --- [ ROUTE UNTUK VERCEL ] ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.get_json(force=True))
        bot.process_new_updates([update])
        return "OK", 200
    return "Joni @SheJua is Online! 🚀", 200

# --- [ FITUR COMMANDS ] ---
@bot.message_handler(commands=['imdb'])
def imdb_info(m):
    query = m.text.replace('/imdb', '').strip()
    if not query:
        bot.reply_to(m, "Kasih judul filmnya dong sob! Contoh: `/imdb Inception`")
        return
    bot.send_chat_action(m.chat.id, 'typing')
    jawaban = joni_brain(f"Berikan info detail IMDB untuk film: {query}", m.from_user.first_name)
    bot.reply_to(m, jawaban)

@bot.message_handler(func=lambda m: True)
def auto_chat(m):
    is_sob = m.text and "sob" in m.text.lower()
    is_reply = m.reply_to_message and m.reply_to_message.from_user.id == bot.get_me().id
    if is_sob or is_reply or m.chat.type == 'private':
        bot.send_chat_action(m.chat.id, 'typing')
        jawaban = joni_brain(m.text, m.from_user.first_name)
        bot.reply_to(m, jawaban)

# --- [ SOLUSI ERROR 500 VERCEL ] ---
# Baris ini SANGAT PENTING untuk mengatasi error 'issubclass' di log kamu
def handler(request):
    return app(request)
