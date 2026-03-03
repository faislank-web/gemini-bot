import os, requests, telebot, re
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- [ KONFIGURASI ] ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
G_KEY = os.getenv("GEMINI_API_KEY")
TMDB_KEY = "60b54f676451a947d100062a420942d9" 
G_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={G_KEY}"

ADMIN_ID = 8227188993 
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- [ OTAK JONI: INGATAN PERSONAL ] ---
def joni_brain(text, name, username, mode="chat"):
    # Joni diberikan konteks siapa yang bicara agar tidak tertukar
    if mode == "detail":
        prompt = (f"Berikan info film sangat lengkap untuk Kak {name} (@{username}). "
                  f"Detail film: {text}. FORMAT: 🎬 *Judul (Tahun)*, ⭐️ *Rating*, 📅 *Rilis*, ⏳ *Durasi*, 🎭 *Genre*, 📝 *Sinopsis*. "
                  f"Sapa dia di awal dengan asik.")
    else:
        prompt = (f"Kamu Joni, manusia asli pakar film @SheJua. Kamu sedang ngobrol dengan {name} (@{username}). "
                  f"JANGAN SEBUT BOT. Jawab sangat singkat & gaul: {text}")
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(G_URL, json=payload, timeout=20)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except: return f"Duh sob {name}, Joni lagi nge-lag dikit nih. 🍿"

# --- [ TOMBOL ADMIN & IDENTITAS ] ---
def admin_markup(name, username):
    markup = InlineKeyboardMarkup()
    # Menampilkan info penanya di bawah tombol agar tidak tertukar
    markup.add(InlineKeyboardButton(f"🔍 Search by: {name}", callback_data="none"))
    markup.add(InlineKeyboardButton("📞 Hubungi Admin", url="https://t.me/filmberbobot"))
    return markup

# --- [ FITUR /IMDB: DATA TMDB ] ---
@bot.message_handler(commands=['imdb'])
def imdb_search(m):
    query = m.text.replace('/imdb', '').strip()
    name, user = m.from_user.first_name, m.from_user.username or "User"
    
    if not query:
        bot.reply_to(m, f"Kasih judul filmnya dong sob {name}!", reply_markup=admin_markup(name, user))
        return
    
    bot.send_chat_action(m.chat.id, 'typing')
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_KEY}&query={query}&language=id-ID"
    results = requests.get(url).json().get('results', [])
    
    if not results:
        bot.reply_to(m, f"Maaf sob {name}, film itu nggak ada di database.", reply_markup=admin_markup(name, user))
        return

    # JIKA BANYAK PILIHAN
    markup = InlineKeyboardMarkup()
    for film in results[:8]:
        tgl = film.get('release_date', '????')[:4]
        # Callback data membawa info agar saat diklik Joni tetap ingat siapa yang klik
        markup.add(InlineKeyboardButton(f"🎬 {film['title']} ({tgl})", callback_data=f"tmdb_{film['id']}"))
    
    markup.add(InlineKeyboardButton(f"👤 Untuk: {name}", callback_data="none"))
    markup.add(InlineKeyboardButton("📞 Hubungi Admin", url="https://t.me/filmberbobot"))
    bot.reply_to(m, f"Joni nemu daftar film buat Kak {name} nih. Pilih yang mana?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('tmdb_'))
def callback_tmdb(call):
    movie_id = call.data.replace('tmdb_', '')
    name, user = call.from_user.first_name, call.from_user.username or "User"
    
    bot.answer_callback_query(call.id, f"Sabar ya {name}...")
    
    # Ambil detail dari TMDB
    m_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_KEY}&language=id-ID"
    m = requests.get(m_url).json()
    poster = f"https://image.tmdb.org/t/p/w500{m.get('poster_path')}" if m.get('poster_path') else None
    
    # Joni Brain buat ngerapihin teks detail dengan sentuhan personal
    raw_info = f"Judul: {m.get('title')}, Rating: {m.get('vote_average')}, Sinopsis: {m.get('overview')}"
    detail_text = joni_brain(raw_info, name, user, mode="detail")
    
    if poster:
        bot.send_photo(call.message.chat.id, poster, caption=detail_text, parse_mode="Markdown", reply_markup=admin_markup(name, user))
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        bot.edit_message_text(detail_text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=admin_markup(name, user))

# --- [ CHAT BIASA: INGAT ORANG YANG BERBEDA ] ---
@bot.message_handler(func=lambda m: True)
def group_chat(m):
    name, user = m.from_user.first_name, m.from_user.username or "User"
    
    # Proteksi Japri
    if m.chat.type == 'private' and m.from_user.id != ADMIN_ID:
        bot.reply_to(m, "Maaf sob, Joni cuma bisa dipake di grup @SheJua!", reply_markup=admin_markup(name, user))
        return

    # Trigger Chat (kata 'sob' atau Reply)
    is_sob = m.text and "sob" in m.text.lower()
    is_reply = m.reply_to_message and m.reply_to_message.from_user.id == bot.get_me().id
    
    if is_sob or is_reply or (m.chat.type == 'private' and m.from_user.id == ADMIN_ID):
        bot.send_chat_action(m.chat.id, 'typing')
        # Joni menjawab secara personal berdasarkan siapa yang mengirim pesan
        jawaban = joni_brain(m.text, name, user)
        bot.reply_to(m, jawaban, reply_markup=admin_markup(name, user))

# --- [ VERCEL HANDLER ] ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.get_json(force=True))
        bot.process_new_updates([update])
        return "OK", 200
    return "Joni @SheJua is Online! 🚀", 200

def handler(request):
    return app(request)
