import os, requests, telebot
from flask import Flask, request

# Konfigurasi dari Vercel
TOKEN = os.getenv("TELEGRAM_TOKEN")
G_KEY = os.getenv("GEMINI_API_KEY")
ADMIN = os.getenv("MY_USER_ID")
G_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={G_KEY}"

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

def get_ai(text, name):
    prompt = f"Kamu Joni, manusia pakar film di @SheJua. Jawab santai. User: {name}. Tanya: {text}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(G_URL, json=payload, timeout=10)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "Aduh sob, Joni lagi pening habis maraton film. Coba lagi ya! 🍿"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.get_json(force=True))
        bot.process_new_updates([update])
        return "OK", 200
    return "Joni @SheJua is Online! 🚀", 200

@bot.message_handler(func=lambda m: True)
def reply(m):
    is_admin = m.chat.type == 'private' and str(m.from_user.id) == str(ADMIN)
    is_sob = m.text and "sob" in m.text.lower()
    if is_admin or is_sob or (m.reply_to_message and m.reply_to_message.from_user.id == bot.get_me().id):
        bot.send_chat_action(m.chat.id, 'typing')
        bot.reply_to(m, get_ai(m.text, m.from_user.first_name))

# Pintu masuk utama Vercel
def handler(request):
    return app(request)
