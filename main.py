import os
import requests
import telebot
from telebot import types
import google.generativeai as genai
from flask import Flask, request

# --- [ DATA AKSES ] ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
ZEABUR_URL = os.environ.get("ZEABUR_WEB_URL")
TMDB_KEY = "61e2290429798c561450eb56b26de19b"

# --- [ KONFIGURASI AI ] ---
genai.configure(api_key=GEMINI_KEY)
instruction = (
    "Kamu adalah pakar film profesional dengan akses info film terbaru 2025-2026. "
    "Berikan sinopsis, pemeran, dan sutradara dengan cerdas. "
    "Jangan awali dengan 'Halo'. Panggil 'sob' hanya jika di grup. "
    "Jika ditanya di chat personal, jawablah secara langsung dan detail."
)
model_ai = genai.GenerativeModel('gemini-1.5-flash', system_instruction=instruction)

user_sessions = {}
bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

def admin_button():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("☎️ Hubungi Admin", url="https://t.me/filmberbobot"))
    return markup

def get_user_name(message):
    return message.from_user.first_name if message.from_user.first_name else message.from_user.username

# --- [ LOGIKA DETAIL FILM - TAMPILAN RAPI ] ---
def get_tmdb_detail(m_id, u_name):
    url = f"https://api.themoviedb.org/3/movie/{m_id}?api_key={TMDB_KEY}&language=id-ID&append_to_response=credits"
    try:
        res = requests.get(url).json()
        p_path = res.get('poster_path')
        p_url = f"https://image.tmdb.org/t/p/w500{p_path}" if p_path else None
        
        title = res.get('title', 'Unknown').upper()
        year = res.get('release_date', '????')[:4]
        rating = res.get('vote_average', 0)
        stars = "⭐" * int(rating/2) if rating > 0 else "🌑"
        genres = ", ".join([g['name'] for g in res.get('genres', [])])
        cast = ", ".join([c['name'] for c in res.get('credits', {}).get('cast', [])[:3]])
        runtime = f"{res.get('runtime', 0)} Menit"
        plot = res.get('overview', 'Sinopsis belum tersedia.')

        # Caption Tanpa Bold Berlebih agar tidak berantakan
        caption = (
            f"🎬 {title} ({year})\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🌟 Rating : {rating:.1f}/10 {stars}\n"
            f"🎭 Genre  : {genres}\n"
            f"⏱ Durasi : {runtime}\n"
            f"👥 Cast    : {cast}\n\n"
            f"📖 SINOPSIS :\n"
            f"{plot[:450] + '...' if len(plot) > 450 else plot}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Requested by: Kak {u_name}"
        )
        return caption, p_url
    except:
        return None, None

@bot.message_handler(commands=['imdb', 'sob'])
def search_movie(message):
    u_name = get_user_name(message)
    query = message.text.split(' ', 1)[1] if len(message.text.split(' ')) > 1 else None
    if not query:
        bot.reply_to(message, f"Kak {u_name}, ketik judul filmnya!", reply_markup=admin_button())
        return

    try:
        res = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_KEY}&query={query}&language=id-ID").json()
        if not res.get('results'):
            bot.reply_to(message, f"❌ Film {query} tidak ditemukan.", reply_markup=admin_button())
            return

        markup = types.InlineKeyboardMarkup()
        for m in res['results'][:5]:
            label = f"🎬 {m.get('title')} ({m.get('release_date','????')[:4]})"
            markup.add(types.InlineKeyboardButton(label, callback_data=f"m_{m['id']}"))
        
        bot.reply_to(message, f"🔍 HASIL PENCARIAN : {query.upper()}", reply_markup=markup)
    except:
        bot.reply_to(message, "Database sedang sibuk, coba lagi nanti ya!", reply_markup=admin_button())

@bot.callback_query_handler(func=lambda call: call.data.startswith('m_'))
def callback_detail(call):
    m_id = call.data.split('_')[1]
    u_name = get_user_name(call)
    cap, post = get_tmdb_detail(m_id, u_name)
    if cap:
        if post: bot.send_photo(call.message.chat.id, post, caption=cap, reply_markup=admin_button())
        else: bot.send_message(call.message.chat.id, cap, reply_markup=admin_button())
        bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda m: True)
def chat_ai(message):
    u_id = message.from_user.id
    u_name = get_user_name(message)
    teks = message.text.lower()
    is_private = message.chat.type == 'private'
    is_reply_to_me = message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id
    
    if is_private or ("sob" in teks and is_reply_to_me):
        try:
            if u_id not in user_sessions:
                user_sessions[u_id] = model_ai.start_chat(history=[])
            response = user_sessions[u_id].send_message(message.text)
            bot.reply_to(message, f"Kak {u_name}, {response.text}", reply_markup=admin_button())
        except Exception as e:
            # Jika AI error, berikan jawaban cerdas manual sementara
            bot.reply_to(message, f"Kak {u_name}, sepertinya saya butuh waktu untuk berpikir. Tanya film lain dulu ya!", reply_markup=admin_button())

@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def get_message():
    if request.headers.get('content-type') == 'application/json':
        bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
        return "OK", 200
    return "Forbidden", 403

@app.route('/')
def setup():
    clean_url = ZEABUR_URL.replace("https://", "").replace("http://", "").strip("/")
    bot.remove_webhook()
    bot.set_webhook(url=f"https://{clean_url}/{TELEGRAM_TOKEN}")
    return "<h1>📍 Upload Complete Selamat Menyaksikan</h1>", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
