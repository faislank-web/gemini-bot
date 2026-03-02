import os, requests, telebot, datetime, pytz, re, random
from flask import Flask, request

# --- [ AMBIL DATA DARI VERCEL SETTINGS ] ---
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
        return f"Waduh Kak {name}, Joni lagi sibuk sortir film. Coba lagi ya! 🍿"
    except:
        return f"Sori sob, Joni lagi pening dikit. Coba lagi ya! 🙏"

# --- [ HANDLER UTAMA ] ---
@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.get_json())
        bot.process_new_updates([update])
        return "OK", 200
    return "Joni @SheJua is Online! 🚀", 200

# --- [ FITUR CHAT ] ---
@bot.message_handler(func=lambda m: True)
def group_chat(m):
    if "sob" in m.text.lower() or (m.reply_to_message and m.reply_to_message.from_user.id == bot.get_me().id):
        bot.send_chat_action(m.chat.id, 'typing')
        jawaban = get_response(m.text, m.from_user.first_name)
        bot.reply_to(m, jawaban)

# --- [ MANTRA SAKTI VERCEL ] ---
# Tanpa ini, Vercel akan kasih Error 500 terus!
def handler(request):
    return app(request)
