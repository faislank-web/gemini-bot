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
    "Kamu adalah pakar film profesional tahun 2026. Jawablah dengan cerdas dan detail. "
    "Berikan sinopsis, pemeran, dan sutradara jika ditanya soal film. "
    "Jangan gunakan kata 'Halo'. Di chat personal, langsung jawab. "
    "Di grup, panggil 'sob' dan jawab jika di-reply."
)
model_ai = genai.GenerativeModel('gemini-1.5-flash', system_instruction=instruction)

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

def admin_button():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("☎️ Hubungi Admin", url="https://t.me/filmberbobot"))
    return markup

# --- [ SEARCH FILM TMDB ] ---
def get_tmdb_detail(m_id, u_name):
    url = f"https://api.themoviedb.org/3/movie/{m_id}?api_key={TMDB_KEY}&language=id-ID&append_to_response=credits"
    try:
        res = requests.get(url).json()
        title = res.get('title', 'Unknown').upper()
        year = res.get('release_date', '????')[:4]
        rating = res.get('vote_average', 0)
        stars = "⭐" * int(rating/2) if rating > 0 else "🌑"
        genres = ", ".join([g['name'] for g in res.get('genres', [])])
        cast = ", ".join([c['name'] for c in res.get('credits', {}).get('cast', [])[:3]])
        plot = res.get('overview', 'Sinopsis belum tersedia.')
        p_url = f"https://image.tmdb.org/t/p/w500{res.get('poster_path')}" if res.get('poster_path') else None

        caption = (
            f"🎬 {title} ({year})\n"
            f"--------------------------------------\n\n"
            f"🌟 Rating : {rating:.1f}/10 {stars}\n"
            f"🎭 Genre  : {genres}\n"
            f"👥 Cast   : {cast}\n\n"
            f"📖 SINOPSIS :\n"
            f"{plot[:500] + '...' if len(plot) > 500 else plot}\n\n"
            f"--------------------------------------\n"
            f"👤 User: Kak {u_name}"
        )
        return caption, p_url
    except: return "Gagal memuat detail film.", None

@bot.message_handler(commands=['imdb', 'sob'])
def search_movie(message):
    query = message.text.split(' ', 1)[1] if len(message.text.split(' ')) > 1 else None
    if not query:
        bot.reply_to(message, "Ketik judul filmnya Kak!")
        return
    try:
        res = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_KEY}&query={query}&language=id-ID").json()
        if not res.get('results'):
            bot.reply_to(message, "Film tidak ditemukan.")
            return
        markup = types.InlineKeyboardMarkup()
        for m in res['results'][:5]:
            markup.add(types.InlineKeyboardButton(f"🎬 {m.get('title')} ({m.get('release_date','????')[:4]})", callback_data=f"m_{m['id']}"))
        bot.reply_to(message, f"🔍 HASIL: {query.upper()}", reply_markup=markup)
    except: bot.reply_to(message, "Error database.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('m_'))
def callback_detail(call):
    cap, post = get_tmdb_detail(call.data.split('_')[1], call.from_user.first_name)
    if post: bot.send_photo(call.message.chat.id, post, caption=cap, reply_markup=admin_button())
    else: bot.send_message(call.message.chat.id, cap, reply_markup=admin_button())
    bot.delete_message(call.message.chat.id, call.message.message_id)

# --- [ CHAT AI: LANGSUNG JAWAB (ANTI-BODOH) ] ---
@bot.message_handler(func=lambda m: True)
def chat_ai(message):
    is_private = message.chat.type == 'private'
    is_reply = message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id

    if is_private or (is_reply and "sob" in message.text.lower()):
        try:
            # Menggunakan generate_content langsung (Tanpa History) agar hemat memori Zeabur
            response = model_ai.generate_content(message.text)
            bot.reply_to(message, f"Kak {message.from_user.first_name}, {response.text}", reply_markup=admin_button())
        except:
            bot.reply_to(message, "Lagi sibuk nih Kak, coba tanya lagi ya!", reply_markup=admin_button())

@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def get_message():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return "OK", 200

@app.route('/')
def setup():
    url = ZEABUR_URL.replace("https://", "").replace("http://", "").strip("/")
    bot.remove_webhook()
    bot.set_webhook(url=f"https://{url}/{TELEGRAM_TOKEN}")
    return "<h1>📍 Upload Complete Selamat Menyaksikan</h1>", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
