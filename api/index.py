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

# --- [ OTAK JONI: MULTI-USER MEMORY ] ---
def joni_brain(text, name, username, mode="chat"):
    if mode == "detail":
        prompt = (f"Kamu Joni. Berikan info film untuk Kak {name} (@{username}). "
                  f"Data film: {text}. Format: 🎬 *Judul (Tahun)*, ⭐️ *Rating*, 📅 *Rilis*, ⏳ *Durasi*, 🎭 *Genre*, 📝 *Sinopsis*. "
                  f"Sapa dia dengan ramah di awal.")
    else:
        prompt = f"Kamu Joni, asisten film @SheJua. Kamu bicara dengan {name} (@{username}). Jawab gaul & singkat: {text}"
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(G_URL, json=payload, timeout=20)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except: return f"Aduh sob {name}, Joni lagi pening. 🍿"

# --- [ TOMBOL ADMIN + IDENTITAS ] ---
def admin_markup(name):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(f"👤 Untuk: {name}", callback_data="none"))
    markup.add(InlineKeyboardButton("📞 Hubungi Admin", url="https://t.me/filmberbobot"))
    return markup

# --- [ FITUR /IMDB ] ---
@bot.message_handler(commands=['imdb'])
def imdb_search(m):
    query = m.text.replace('/imdb', '').strip()
    name = m.from_user.first_name
    
    if not query:
        bot.reply_to(m, f"Kasih judul filmnya sob {name}!", reply_markup=admin_markup(name))
        return
    
    bot.send_chat_action(m.chat.id, 'typing')
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_KEY}&query={query}&language=id-ID"
    try:
        results = requests.get(url, timeout=10).json().get('results', [])
        if not results:
            bot.reply_to(m, f"Nggak ketemu sob {name}. Coba judul lain.", reply_markup=admin_markup(name))
            return

        markup = InlineKeyboardMarkup()
        for film in results[:8]:
            tgl = film.get('release_date', '????')[:4]
            # Simpan movie_id di callback
            markup.add(InlineKeyboardButton(f"🎬 {film['title']} ({tgl})", callback_data=f"tmdb_{film['id']}"))
        
        markup.add(InlineKeyboardButton(f"👤 Search by: {name}", callback_data="none"))
        markup.add(InlineKeyboardButton("📞 Hubungi Admin", url="https://t.me/filmberbobot"))
        bot.reply_to(m, f"Pilih filmnya Kak {name}:", reply_markup=markup)
    except:
        bot.reply_to(m, "Database TMDB lagi sibuk sob!")

@bot.callback_query_handler(func=lambda call: call.data.startswith('tmdb_'))
def callback_tmdb(call):
    movie_id = call.data.replace('tmdb_', '')
    name = call.from_user.first_name
    username = call.from_user.username or "User"
    
    bot.answer_callback_query(call.id, f"Sabar ya {name}...")
    
    try:
        m_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_KEY}&language=id-ID"
        m = requests.get(m_url, timeout=10).json()
        poster = f"https://image.tmdb.org/t/p/w500{m.get('poster_path')}" if m.get('poster_path') else None
        
        raw_info = f"Judul: {m.get('title')}, Rating: {m.get('vote_average')}, Sinopsis: {m.get('overview')}"
        detail_text = joni_brain(raw_info, name, username, mode="detail")
        
        if poster:
            bot.send_photo(call.message.chat.id, poster, caption=detail_text, parse_mode="Markdown", reply_markup=admin_markup(name))
            bot.delete_message(call.message.chat.id, call.message.message_id)
        else:
            bot.edit_message_text(detail_text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=admin_markup(name))
    except:
        bot.send_message(call.message.chat.id, "Gagal narik detail filmnya sob!")

# --- [ CHAT BIASA & PROTEKSI ] ---
@bot.message_handler(func=lambda m: True)
def group_chat(m):
    name = m.from_user.first_name
    username = m.from_user.username or "User"
    
    if m.chat.type == 'private' and m.from_user.id != ADMIN_ID:
        bot.reply_to(m, "Maaf sob, Joni cuma buat grup @SheJua!", reply_markup=admin_markup(name))
        return

    is_sob = m.text and "sob" in m.text.lower()
    is_reply = m.reply_to_message and m.reply_to_message.from_user.id == bot.get_me().id
    
    if is_sob or is_reply or (m.chat.type == 'private' and m.from_user.id == ADMIN_ID):
        bot.send_chat_action(m.chat.id, 'typing')
        jawaban = joni_brain(m.text, name, username)
        bot.reply_to(m, jawaban, reply_markup=admin_markup(name))

# --- [ VERCEL HANDLER ] ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            update = telebot.types.Update.de_json(request.get_json(force=True))
            bot.process_new_updates([update])
            return "OK", 200
        except Exception as e:
            return str(e), 500
    return "Joni @SheJua is Ready! 🚀", 200

def handler(request):
    return app(request)
