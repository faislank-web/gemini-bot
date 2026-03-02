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

# Kita pakai satu model utama yang paling stabil saja dulu biar nggak bentrok v1beta
MODEL_NAME = 'gemini-1.5-flash'

SYS_INSTRUCT = (
    "Kamu adalah Joni, manusia asli yang pakar film dan sangat ramah. "
    "Bicaralah seperti teman nongkrong, gunakan banyak emotikon. "
    "Jangan pernah bilang kamu AI atau bot. "
    "Kalau ada yang tanya film, ceritakan sinopsis dan detailnya dengan asik. "
    "Di chat personal, langsung jawab. Di grup, panggil 'sob' kalau di-reply."
)

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

def admin_button():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("☎️ Chat Admin", url="https://t.me/filmberbobot"))
    return markup

# --- [ FUNGSI IMDB ] ---
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

@bot.message_handler(commands=['start'])
def send_welcome(message):
    nama = message.from_user.first_name
    bot.reply_to(message, f"Eh, Kak {nama}! 👋 Mau tanya film apa hari ini? Ketik judulnya ya, atau pake /imdb biar makin keren infonya! Oiya cek /rules juga ya. 🎬", reply_markup=admin_button())

@bot.message_handler(commands=['rules'])
def send_rules(message):
    rules = "📜 **ATURAN JONI**\n1. Santai aja Kak.\n2. Cari film pake /imdb [judul].\n3. Request? Ketik: `#request Judul Tahun`."
    bot.reply_to(message, rules, parse_mode="Markdown")

@bot.message_handler(commands=['imdb'])
def search_movie(message):
    query = message.text.split(' ', 1)[1] if len(message.text.split(' ')) > 1 else None
    if not query:
        bot.reply_to(message, "Ketik judul filmnya Kak! Contoh: /imdb Avatar")
        return
    res = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_KEY}&query={query}&language=id-ID").json()
    if not res.get('results'):
        bot.reply_to(message, "Nggak ketemu filmnya Kak. 😅")
        return
    markup = types.InlineKeyboardMarkup()
    for m in res['results'][:5]:
        markup.add(types.InlineKeyboardButton(f"🎬 {m.get('title')} ({m.get('release_date','????')[:4]})", callback_data=f"m_{m['id']}"))
    bot.reply_to(message, f"🔍 HASIL CARI: {query.upper()}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('m_'))
def callback_detail(call):
    cap, post = get_tmdb_detail(call.data.split('_')[1], call.from_user.first_name)
    if post: bot.send_photo(call.message.chat.id, post, caption=cap, reply_markup=admin_button())
    else: bot.send_message(call.message.chat.id, cap, reply_markup=admin_button())

@bot.message_handler(func=lambda m: "#request" in m.text.lower())
def handle_movie_request(message):
    text = message.text.lower().replace("#request", "").strip()
    words = text.split()
    if len(words) < 2:
        bot.reply_to(message, "Format salah Kak! Harus `#request Judul Tahun`. Contoh: `#request Avatar 2022`.")
    else:
        bot.reply_to(message, f"Sip, request film {text} sudah Joni simpan ya! 👌")
        bot.forward_message(message.from_user.id, message.chat.id, message.message_id)

@bot.message_handler(func=lambda m: True)
def chat_ai(message):
    is_private = message.chat.type == 'private'
    is_reply = message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id

    if is_private or (is_reply and "sob" in message.text.lower()):
        try:
            # INI KUNCINYA: Jangan pake models/ dan jangan biarkan library pilih v1beta
            model = genai.GenerativeModel(MODEL_NAME)
            response = model.generate_content(f"{SYS_INSTRUCT}\n\nPertanyaan user: {message.text}")
            bot.reply_to(message, f"Kak {message.from_user.first_name}, {response.text}", reply_markup=admin_button())
        except Exception as e:
            print(f"Error fatal: {e}")
            bot.reply_to(message, "Duh Kak, Joni lagi dipanggil admin sebentar. Coba tanya lagi ya! 🙏")

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
