import os, requests, telebot, re
from flask import Flask, request

# --- [ KONFIGURASI ] ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
G_KEY = os.getenv("GEMINI_API_KEY")
TMDB_KEY = "60b54f676451a947d100062a420942d9"
G_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={G_KEY}"

ADMIN_ID = 8227188993 
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- [ TOMBOL ADMIN + INFO PENANYA ] ---
def create_markup(name, movie_results=None):
    markup = telebot.types.InlineKeyboardMarkup()
    if movie_results:
        for film in movie_results[:8]:
            tgl = film.get('release_date', '????')[:4]
            markup.add(telebot.types.InlineKeyboardButton(f"🎬 {film['title']} ({tgl})", callback_data=f"tmdb_{film['id']}"))
    
    markup.add(telebot.types.InlineKeyboardButton(f"👤 Penanya: {name}", callback_data="none"))
    markup.add(telebot.types.InlineKeyboardButton("📞 Hubungi Admin", url="https://t.me/filmberbobot"))
    return markup

# --- [ FITUR #REQUEST: KIRIM KE ADMIN ] ---
@bot.message_handler(func=lambda m: m.text and m.text.startswith('#request'))
def handle_request(m):
    name = m.from_user.first_name
    username = f"@{m.from_user.username}" if m.from_user.username else "Tanpa Username"
    
    # Mencari pola: #request [Judul Bebas] [4 Digit Tahun]
    pattern = r"#request\s+(.+)\s+(\d{4})"
    match = re.search(pattern, m.text)
    
    if match:
        judul = match.group(1).strip()
        tahun = match.group(2)
        
        # Pesan rapi buat masuk ke Saved Messages kamu
        laporan_admin = (f"🚀 **REKAPAN REQUEST BARU**\n\n"
                         f"👤 **User:** {name} ({username})\n"
                         f"🎬 **Film:** {judul}\n"
                         f"📅 **Tahun:** {tahun}\n"
                         f"📍 **Status:** Menunggu Admin")
        
        try:
            bot.send_message(ADMIN_ID, laporan_admin, parse_mode="Markdown")
            bot.reply_to(m, f"✅ Sip Kak {name}, request **{judul} ({tahun})** sudah Joni catat dan lapor ke Admin! 🥂", reply_markup=create_markup(name))
        except:
            bot.reply_to(m, f"✅ Request diterima, tapi Joni gagal kirim japri ke Admin. Pastikan Admin sudah /start di bot ini ya!", reply_markup=create_markup(name))
    else:
        bot.reply_to(m, f"⚠️ Salah format sob {name}!\nContoh: `#request Avatar 2009`", reply_markup=create_markup(name))

# --- [ /IMDB & CALLBACK (TMDB) ] ---
@bot.message_handler(commands=['imdb'])
def imdb_cmd(m):
    query = m.text.replace('/imdb', '').strip()
    name = m.from_user.first_name
    if not query:
        bot.reply_to(m, "Judulnya apa sob?", reply_markup=create_markup(name))
        return
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_KEY}&query={query}&language=id-ID"
    res = requests.get(url).json().get('results', [])
    bot.reply_to(m, f"Hasil buat Kak {name}:", reply_markup=create_markup(name, res))

@bot.callback_query_handler(func=lambda call: call.data.startswith('tmdb_'))
def handle_callback(call):
    name = call.from_user.first_name
    movie_id = call.data.replace('tmdb_', '')
    m_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_KEY}&language=id-ID"
    m = requests.get(m_url).json()
    poster = f"https://image.tmdb.org/t/p/w500{m.get('poster_path')}" if m.get('poster_path') else None
    txt = (f"🎬 *{m.get('title')} ({m.get('release_date', '????')[:4]})*\n\n"
           f"⭐️ *Rating:* {m.get('vote_average')}/10\n"
           f"📝 *Sinopsis:* {m.get('overview', 'Gak ada sinopsis.')[:400]}...")
    
    if poster:
        bot.send_photo(call.message.chat.id, poster, caption=txt, parse_mode="Markdown", reply_markup=create_markup(name))
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=create_markup(name))

# --- [ CHAT AUTO & PROTEKSI ] ---
@bot.message_handler(func=lambda m: True)
def auto_chat(m):
    name = m.from_user.first_name
    if m.chat.type == 'private' and m.from_user.id != ADMIN_ID:
        bot.reply_to(m, "Hanya bisa di grup @SheJua sob!", reply_markup=create_markup(name))
        return
    if m.text and ("sob" in m.text.lower() or (m.reply_to_message and m.reply_to_message.from_user.id == bot.get_me().id)):
        prompt = f"Kamu Joni @SheJua. Sapa {name}. Jawab sangat singkat & gaul: {m.text}"
        res = requests.post(G_URL, json={"contents": [{"parts": [{"text": prompt}]}]}).json()
        ans = res['candidates'][0]['content']['parts'][0]['text']
        bot.reply_to(m, ans, reply_markup=create_markup(name))

# --- [ VERCEL CORE ] ---
@app.route('/', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_json(force=True))
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def index():
    return "Joni Online!", 200
