import os, requests, telebot, json
from telebot import types
from flask import Flask, request

# --- [ KONFIGURASI ] ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
ZEABUR_URL = os.environ.get("ZEABUR_WEB_URL")
TMDB_KEY = "61e2290429798c561450eb56b26de19b"

# Pakai model 8b yang lebih ringan dan jarang 404
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-8b:generateContent?key={GEMINI_KEY}"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# --- [ TOMBOL ] ---
def movie_buttons():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎬 Nonton Disini", url="https://t.me/SheJua"),
        types.InlineKeyboardButton("☎️ Chat Admin", url="https://t.me/filmberbobot")
    )
    return markup

# --- [ FUNGSI AI ] ---
def get_ai_response(text):
    payload = {
        "contents": [{"parts": [{"text": f"Kamu adalah Joni, manusia pakar film. Jawab santai sebagai teman: {text}"}]}]
    }
    try:
        res = requests.post(GEMINI_URL, json=payload, timeout=10)
        data = res.json()
        return data['candidates'][0]['content']['parts'][0]['text']
    except:
        return None

# --- [ FUNGSI TMDB ] ---
def get_movie_detail(m_id, u_name):
    url = f"https://api.themoviedb.org/3/movie/{m_id}?api_key={TMDB_KEY}&language=id-ID"
    try:
        res = requests.get(url).json()
        t = res.get('title', 'UPPER').upper()
        d = res.get('release_date', '????')
        m = res.get('runtime', 0)
        p = res.get('overview', 'Sinopsis belum tersedia.')
        img = f"https://image.tmdb.org/t/p/w500{res.get('poster_path')}" if res.get('poster_path') else None
        
        cap = (
            f"🎬 **{t}** ({d[:4]})\n"
            f"--------------------------------------\n"
            f"📅 **Rilis** : {d}\n"
            f"⏳ **Durasi** : {m} Menit\n"
            f"🌟 **Rating** : {res.get('vote_average', 0):.1f}/10\n\n"
            f"📖 **SINOPSIS** :\n{p[:500]}...\n"
            f"--------------------------------------\n"
            f"👤 User: Kak {u_name}"
        )
        return cap, img
    except: return "Gagal memuat detail.", None

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, f"Eh, Kak {m.from_user.first_name}! 👋 Mau tanya film apa? Ketik judulnya atau pake /imdb ya! 🎬", reply_markup=movie_buttons())

@bot.message_handler(commands=['imdb'])
def imdb(m):
    query = m.text.split(' ', 1)[1] if len(m.text.split()) > 1 else None
    if not query: return bot.reply_to(m, "Ketik judulnya Kak!")
    
    res = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_KEY}&query={query}&language=id-ID").json()
    if not res.get('results'): return bot.reply_to(m, "Film nggak ketemu.")
    
    markup = types.InlineKeyboardMarkup()
    for f in res['results'][:5]:
        markup.add(types.InlineKeyboardButton(f"🎬 {f['title']} ({f.get('release_date','?')[:4]})", callback_data=f"idx_{f['id']}"))
    bot.reply_to(m, f"🔍 HASIL CARI: {query.upper()}", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith('idx_'))
def detail(c):
    cap, img = get_movie_detail(c.data.split('_')[1], c.from_user.first_name)
    if img: bot.send_photo(c.message.chat.id, img, caption=cap, parse_mode="Markdown", reply_markup=movie_buttons())
    else: bot.send_message(c.message.chat.id, cap, parse_mode="Markdown", reply_markup=movie_buttons())

@bot.message_handler(func=lambda m: True)
def chat(m):
    if m.chat.type == 'private' or (m.reply_to_message and m.reply_to_message.from_user.id == bot.get_me().id):
        ans = get_ai_response(m.text)
        if ans: bot.reply_to(m, f"Kak {m.from_user.first_name}, {ans}", reply_markup=movie_buttons())
        else: bot.reply_to(m, "Aduh Kak, Joni lagi dipanggil admin sebentar. Coba lagi ya! 🙏")

@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return "OK", 200

@app.route('/')
def setup():
    bot.remove_webhook()
    bot.set_webhook(url=f"{ZEABUR_URL}/{TELEGRAM_TOKEN}")
    return "<h1>📍 Upload Complete Selamat Menyaksikan</h1>", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
