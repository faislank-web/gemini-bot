import os, requests, telebot
from flask import Flask, request

# Variabel ini harus ada di Vercel Settings
TOKEN = os.getenv("TELEGRAM_TOKEN")
G_KEY = os.getenv("GEMINI_API_KEY")
ADMIN = os.getenv("MY_USER_ID")

G_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={G_KEY}"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Vercel butuh force=True agar JSON terbaca sempurna
        update = telebot.types.Update.de_json(request.get_json(force=True))
        bot.process_new_updates([update])
        return "OK", 200
    return "Joni @SheJua is Online! 🚀", 200

@bot.message_handler(func=lambda m: True)
def reply(m):
    # Joni nyaut kalau ada kata 'sob' atau reply
    if m.text and "sob" in m.text.lower() or (m.reply_to_message and m.reply_to_message.from_user.id == bot.get_me().id):
        prompt = f"Kamu Joni, pakar film @SheJua. Jawab santai. User: {m.from_user.first_name}. Tanya: {m.text}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            res = requests.post(G_URL, json=payload, timeout=10)
            bot.reply_to(m, res.json()['candidates'][0]['content']['parts'][0]['text'])
        except:
            bot.reply_to(m, "Sori sob, Joni lagi pening. Coba lagi ya! 🙏")
