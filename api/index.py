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

# --- [ TOMBOL ADMIN + PERSONAL INFO ] ---
def create_markup(name, results=None):
    markup = telebot.types.InlineKeyboardMarkup()
    if results:
        for film in results[:8]:
            tgl = film.get('release_date', '????')[:4]
            markup.add(telebot.types.InlineKeyboardButton(f"🎬 {film['title']} ({tgl})", callback_data=f"tmdb_{film['id']}"))
    
    markup.add(telebot.types.InlineKeyboardButton(f"👤 Penanya: {name}", callback_data="none"))
    markup.add(telebot.types.InlineKeyboardButton("📞 Hubungi Admin", url="https://t.me/filmberbobot"))
    return markup

# --- [ FITUR #REQUEST: KIRIM KE SAVED MESSAGES ADMIN ] ---
@bot.message_handler(func=lambda m: m.text and m.text.startswith('#request'))
def handle_request(m):
    name = m.from_user.first_name
    username = f"@{m.from_user.username}" if m.from_user.username else "User"
    
    # Mencari pola: #request [Judul] [Tahun]
    match = re.search(r"#request\s+(.+)\s+(\d{4})", m.text)
    
    if match:
        judul, tahun = match.group(1).strip(), match.group(2)
        # Laporan buat kamu
        msg_to_admin = (f"🚀 **REQUEST BARU**\n\n"
                        f"👤 **Dari:** {name} ({username})\n"
                        f"🎬 **Film:** {judul}\n"
                        f"📅 **Tahun:** {tahun}")
        try:
            bot.send_message(ADMIN_ID, msg_to_admin)
            bot.reply_to(m, f"✅ Sip Kak {name}, request film **{judul}** sudah Joni lapor ke Admin!", reply_markup=create_markup(name))
        except:
            bot.reply_to(m, "✅ Request diterima! (Admin: Pastikan sudah /start ke bot ini ya)", reply_markup=create_markup(name))
    else:
        bot.reply_to(m, "⚠️ Format salah sob! Contoh: `#request Joker 2019`", reply_markup=create_markup(name))

# --- [ /IMDB & CALLBACK ] ---
@bot.message_handler(commands=['imdb'])
def imdb_cmd(m):
    query = m.text.replace('/imdb', '').strip()
    name = m.from_user.first_name
    if not query:
        bot.reply_to(m, "Mau cari film apa sob?", reply_markup=create_markup(name))
        return
    
    res = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_KEY}&query={query}&language=id-ID").json().get('results', [])
    bot.reply_to(m, f"Hasil buat Kak {name}:", reply_markup=create_markup(name, res))

@bot.callback_query_handler(func=lambda call: call.data.startswith('tmdb_'))
def handle_tmdb(call):
    name = call.from_user.first_name
    mid = call.data.replace('tmdb_', '')
    m = requests.get(f"https://api.themoviedb.org/3/movie/{mid}?api_key={TMDB_KEY}&language=id-ID").json()
    
    img = f"https://image.tmdb.org/t/p/w500{m.get('poster_path')}" if m.get('poster_path') else None
    txt = (f"🎬 *{m.get('title')} ({m.get('release_date', '????')[:4]})*\n\n"
           f"⭐️ *Rating:* {m.get('vote_average')}/10\n"
           f"📝 *Sinopsis:* {m.get('overview', 'No info.')[:400]}...")

    if img:
        bot.send_photo(call.message.chat.id, img, caption=txt, parse_mode="Markdown", reply_markup=create_markup(name))
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=create_markup(name))

# --- [ CHAT AUTO & PROTEKSI JAPRI ] ---
@bot.message_handler(func=lambda m: True)
def auto_chat(m):
    name = m.from_user.first_name
    if m.chat.type == 'private' and m.from_user.id != ADMIN_ID:
        bot.reply_to(m, "Maaf sob, Joni cuma bisa dipake di grup @SheJua!", reply_markup=create_markup(name))
        return
    
    if m.text and ("sob" in m.text.lower() or (m.reply_to_message and m.reply_to_message.from_user.id == bot.get_me().id)):
        prompt = f"Kamu Joni @SheJua. Sapa {name}. Jawab sangat singkat & gaul: {m.text}"
        res = requests.post(G_URL, json={"contents": [{"parts": [{"text": prompt}]}]}).json()
        ans = res['candidates'][0]['content']['parts'][0]['text']
        bot.reply_to(m, ans, reply_markup=create_markup(name))

# --- [ VERCEL ENTRY - JANGAN PAKAI HANDLER(REQUEST) ] ---
@app.route('/', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_json(force=True))
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def index():
    return "Joni Online!", 200
