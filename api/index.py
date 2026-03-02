import os, requests, telebot, json, re
from flask import Flask, request

# --- [ KONFIGURASI ] ---
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
        f"Sapa Kak {name}. Jawab santai, asik, bantu sortir film, atau bahas teknis download film. "
        f"Pertanyaan: {text}"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(G_URL, json=payload, timeout=15)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return f"Aduh sob {name}, Joni lagi pening dikit habis maraton film. Coba lagi ya! 🍿"

# --- [ HANDLER VERCEL ] ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.get_json(force=True))
        bot.process_new_updates([update])
        return "OK", 200
    return "Joni @SheJua is Online! 🚀", 200

# --- [ FITUR COMMANDS ] ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(m):
    teks = (
        "🎬 **Halo Sob! Joni @SheJua di sini.**\n\n"
        "Joni siap bantu kamu soal film, rating IMDB, atau teknis download.\n"
        "📌 **Perintah:**\n"
        "• `/imdb [judul]` - Cek info film\n"
        "• Panggil 'sob' - Ngobrol santai sama Joni\n"
        "• Reply chat Joni - Lanjut diskusi film"
    )
    bot.reply_to(m, teks, parse_mode="Markdown")

@bot.message_handler(commands=['imdb'])
def imdb_info(m):
    query = m.text.replace('/imdb', '').strip()
    if not query:
        bot.reply_to(m, "Kasih judul filmnya dong sob! Contoh: `/imdb Inception`")
        return
    bot.send_chat_action(m.chat.id, 'typing')
    jawaban = joni_brain(f"Berikan info detail IMDB untuk film: {query}", m.from_user.first_name)
    bot.reply_to(m, jawaban)

# --- [ FITUR CHAT OTOMATIS ] ---
@bot.message_handler(func=lambda m: True)
def group_chat(m):
    # Logika nyaut: Di Private (Admin), Ada kata 'sob', atau Di-Reply
    is_admin = m.chat.type == 'private' and str(m.from_user.id) == str(ADMIN)
    is_sob = m.text and "sob" in m.text.lower()
    is_reply = m.reply_to_message and m.reply_to_message.from_user.id == bot.get_me().id

    if is_admin or is_sob or is_reply:
        bot.send_chat_action(m.chat.id, 'typing')
        jawaban = joni_brain(m.text, m.from_user.first_name)
        bot.reply_to(m, jawaban)

# --- [ MANTRA VERCEL ] ---
def handler(request):
    return app(request)
