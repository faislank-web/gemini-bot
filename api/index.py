import os
import requests
import telebot
from flask import Flask, request

# --- [ KONFIGURASI ] ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
MY_USER_ID = os.getenv("MY_USER_ID")

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"

bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=False)
app = Flask(__name__)

def get_response(text, name):
    prompt = (
        f"Kamu Joni, manusia asli pakar film di grup @SheJua. JANGAN SEBUT DIRIMU AI/BOT. "
        f"Sapa Kak {name}. Jawab santai sebagai teman nongkrong. Pertanyaan: {text}"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(GEMINI_URL, json=payload, timeout=15)
        data = res.json()
        if 'candidates' in data and data['candidates']:
            return data['candidates'][0]['content']['parts'][0]['text']
        return f"Waduh Kak {name}, Joni lagi pening dikit habis maraton film. Coba lagi ya! 🍿"
    except:
        return f"Sori sob, Joni lagi sibuk sortir film terbaru. Tunggu bentar ya! 🙏"

# --- [ HANDLER VERCEL ] ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return "OK", 200
    return "Joni @SheJua is Online! 🚀", 200

# --- [ FITUR CHAT ] ---
@bot.message_handler(func=lambda m: True)
def handle_messages(m):
    # Joni nyaut di Private (Admin) atau di Grup jika ada kata 'sob' atau di-reply
    is_private = m.chat.type == 'private' and str(m.from_user.id) == str(MY_USER_ID)
    is_group = m.chat.type in ['group', 'supergroup'] and ("sob" in m.text.lower() or (m.reply_to_message and m.reply_to_message.from_user.id == bot.get_me().id))
    
    if is_private or is_group:
        bot.send_chat_action(m.chat.id, 'typing')
        jawaban = get_response(m.text, m.from_user.first_name)
        bot.reply_to(m, jawaban)

# --- [ MANTRA SAKTI ] ---
def handler(request):
    return app(request)
