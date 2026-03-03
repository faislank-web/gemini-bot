import os, requests, telebot, re
from flask import Flask, request

# --- [ KONFIGURASI ] ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
G_KEY = os.getenv("GEMINI_API_KEY")
TMDB_KEY = "60b54f676451a947d100062a420942d9"
G_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={G_KEY}"

ADMIN_ID = 8227188993 
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- [ TOMBOL ADMIN + INFO PENANYA ] ---
def create_markup(name, results=None):
    markup = telebot.types.InlineKeyboardMarkup()
    if results:
        for film in results[:8]:
            tgl = film.get('release_date', '????')[:4]
            markup.add(telebot.types.InlineKeyboardButton(f"🎬 {film['title']} ({tgl})", callback_data=f"tmdb_{film['id']}"))
    markup.add(telebot.types.InlineKeyboardButton(f"👤 Penanya: {name}", callback_data="none"))
    markup.add(telebot.types.InlineKeyboardButton("📞 Hubungi Admin", url="https://t.me/filmberbobot"))
    return markup

# --- [ FITUR #REQUEST ] ---
@bot.message_handler(func=lambda m: m.text and m.text.startswith('#request'))
def handle_request(m):
    name = m.from_user.first_name
    match = re.search(r"#request\s+(.+)\s+(\d{4})", m.text)
    if match:
        judul, tahun = match.group(1).strip(), match.group(2)
        try:
            bot.send_message(ADMIN_ID, f"🚀 **REQUEST BARU**\n👤 {name} (@{m.from_user.username})\n🎬 {judul} ({tahun})")
            bot.reply_to(m, f"✅ Sip Kak {name}, request **{judul}** sudah Joni lapor ke Admin!", reply_markup=create_markup(name))
        except:
            bot.reply_to(m, f"✅ Request {judul} diterima!", reply_markup=create_markup(name))

# --- [ IMDB PENCARIAN ] ---
@bot.message_handler(commands=['imdb'])
def imdb_cmd(m):
    query = m.text.replace('/imdb', '').strip()
    name = m.from_user.first_name
    if not query:
        bot.reply_to(m, f"Cari film apa sob {name}?", reply_markup=create_markup(name))
        return
    bot.send_chat_action(m.chat.id, 'typing')
    res = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_KEY}&query={query}&language=id-ID").json().get('results', [])
    bot.reply_to(m, f"Halo Kak {name}, ini hasil pencarian Joni buat kamu:", reply_markup=create_markup(name, res))

@bot.callback_query_handler(func=lambda call: call.data.startswith('tmdb_'))
def handle_tmdb(call):
    name = call.from_user.first_name
    mid = call.data.replace('tmdb_', '')
    bot.answer_callback_query(call.id, f"Sabar ya {name}...")
    m = requests.get(f"https://api.themoviedb.org/3/movie/{mid}?api_key={TMDB_KEY}&language=id-ID").json()
    img = f"https://image.tmdb.org/t/p/w500{m.get('poster_path')}" if m.get('poster_path') else None
    txt = (f"Halo Kak {name}! Ini detail filmnya:\n\n"
           f"🎬 *{m.get('title')} ({m.get('release_date', '????')[:4]})*\n"
           f"⭐️ *Rating:* {m.get('vote_average')}/10\n\n"
           f"📝 *Sinopsis:* {m.get('overview', 'Gak ada info.')[:400]}...")
    if img:
        bot.send_photo(call.message.chat.id, img, caption=txt, parse_mode="Markdown", reply_markup=create_markup(name))
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=create_markup(name))

# --- [ CHAT AUTO ] ---
@bot.message_handler(func=lambda m: True)
def auto_chat(m):
    name = m.from_user.first_name
    if m.chat.type == 'private' and m.from_user.id != ADMIN_ID:
        bot.reply_to(m, "Maaf sob, Joni cuma bisa dipake di grup @SheJua!", reply_markup=create_markup(name))
        return
    if m.text and ("sob" in m.text.lower() or (m.reply_to_message and m.reply_to_message.from_user.id == bot.get_me().id)):
        bot.send_chat_action(m.chat.id, 'typing')
        try:
            # Joni coba pake Gemini
            res = requests.post(G_URL, json={"contents": [{"parts": [{"text": f"Sapa {name} dan jawab gaul: {m.text}"}]}]}, timeout=10).json()
            ans = res['candidates'][0]['content']['parts'][0]['text']
            bot.reply_to(m, ans, reply_markup=create_markup(name))
        except:
            # Kalau Gemini error, Joni jawab manual biar nggak bisu
            bot.reply_to(m, f"Halo Kak {name}! Joni lagi sibuk ngubek database film nih, ada apa sob?", reply_markup=create_markup(name))

# --- [ VERCEL ] ---
@app.route('/', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_json(force=True))
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def index():
    return "Joni Online!", 200
