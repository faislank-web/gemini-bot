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

# DAFTAR MODEL (Tanpa prefix models/ karena library akan menambahkannya sendiri)
MODEL_LIST = ['gemini-1.5-flash', 'gemini-1.5-pro']

SYS_INSTRUCT = (
    "Kamu adalah Joni, manusia asli yang pakar film dan sangat ramah. "
    "Jangan pernah bilang kamu AI atau bot. Bicaralah seperti teman nongkrong. "
    "Kalau ada yang tanya film, ceritakan sinopsis dan detailnya dengan asik. "
    "Di chat personal, langsung jawab. Di grup, panggil 'sob' kalau di-reply."
)

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

def admin_button():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("☎️ Chat Admin", url="https://t.me/filmberbobot"))
    return markup

# --- [ FUNGSI TMDB ] ---
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
    teks = (
        f"Eh, Kak {nama}! 👋 Senang ketemu Kakak lagi.\n\n"
        f"Mau tanya info film apa hari ini? Ketik judulnya aja ya.\n"
        f"Atau pake /imdb [judul] biar lebih lengkap infonya.\n"
        f"Ketik /rules kalau mau lihat aturan main kita.\n"
        f"Ketik #request [judul] [tahun] kalau mau titip film.\n\n"
        f"Selamat menyaksikan! 🎬"
    )
    bot.reply_to(message, teks, reply_markup=admin_button())

@bot.message_handler(commands=['rules'])
def send_rules(message):
    rules = (
        "📜 **ATURAN JONI**\n"
        "---------------------------\n"
        "1. Santai aja Kak, jangan spam ya.\n"
        "2. Cari info film lengkap pake /imdb [judul].\n"
        "3. Mau request? Wajib pake format: `#request Judul Tahun`.\n"
        "4. Tetap sopan biar kita makin akrab!\n"
        "---------------------------"
    )
    bot.reply_to(message, rules, parse_mode="Markdown")

@bot.message_handler(commands=['imdb'])
def search_movie(message):
    query = message.text.split(' ', 1)[1] if len(message.text.split(' ')) > 1 else None
    if not query:
        bot.reply_to(message, "Ketik judul filmnya Kak! Contoh: /imdb Avatar")
        return
    try:
        res = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_KEY}&query={query}&language=id-ID").json()
        if not res.get('results'):
            bot.reply_to(message, "Filmnya nggak ketemu nih Kak.")
            return
        markup = types.InlineKeyboardMarkup()
        for m in res['results'][:5]:
            markup.add(types.InlineKeyboardButton(f"🎬 {m.get('title')} ({m.get('release_date','????')[:4]})", callback_data=f"m_{m['id']}"))
        bot.reply_to(message, f"🔍 HASIL CARI: {query.upper()}", reply_markup=markup)
    except: bot.reply_to(message, "Aduh, lagi pening akses database nih.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('m_'))
def callback_detail(call):
    cap, post = get_tmdb_detail(call.data.split('_')[1], call.from_user.first_name)
    if post: bot.send_photo(call.message.chat.id, post, caption=cap, reply_markup=admin_button())
    else: bot.send_message(call.message.chat.id, cap, reply_markup=admin_button())
    bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda m: "#request" in m.text.lower())
def handle_movie_request(message):
    text = message.text.lower().replace("#request", "").strip()
    words = text.split()
    nama = message.from_user.first_name

    if not text:
        bot.reply_to(message, f"Duh Kak {nama}, tulis judul sama tahunnya dong. Contoh: `#request Avatar 2022`.")
    elif len(words) < 2:
        bot.reply_to(message, f"Maaf ya Kak {nama}, request harus pake tahun biar Joni nggak salah cari. Contoh: `#request {text} 2024`.")
    else:
        bot.reply_to(message, f"Sip, permintaan Kak {nama} sudah Joni simpan! Ditunggu ya.")
        bot.forward_message(message.from_user.id, message.chat.id, message.message_id)

@bot.message_handler(func=lambda m: True)
def chat_ai(message):
    is_private = message.chat.type == 'private'
    is_reply = message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id

    if is_private or (is_reply and "sob" in message.text.lower()):
        response_text = None
        for model_name in MODEL_LIST:
            try:
                # PERBAIKAN KRUSIAL: Tambahkan prefix 'models/' secara manual untuk memancing API yang benar
                model = genai.GenerativeModel(
                    model_name=f"models/{model_name}", 
                    system_instruction=SYS_INSTRUCT
                )
                response = model.generate_content(message.text)
                if response and response.text:
                    response_text = response.text
                    break
            except Exception as e:
                print(f"Gagal pakai {model_name}: {e}")
                continue
        
        if response_text:
            bot.reply_to(message, f"Kak {message.from_user.first_name}, {response_text}", reply_markup=admin_button())
        else:
            bot.reply_to(message, "Aduh, Joni lagi pening nih Kak, coba tanya lagi sedetik lagi ya!")

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
