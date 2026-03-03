import os, requests, telebot, re
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- [ KONFIGURASI AMAN ] ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
G_KEY = os.getenv("GEMINI_API_KEY")
G_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={G_KEY}"

# ID KAMU (Pesan Tersimpan)
TARGET_REQUEST_ID = "8227188993" 

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# --- [ OTAK JONI ] ---
def joni_brain(text, name, is_imdb=False):
    if is_imdb:
        prompt = (f"Halo Joni! Berikan info film lengkap untuk {name} tentang: {text}. "
                  f"FORMAT WAJIB: 🎬 *Judul (Tahun)*, ⭐️ *Rating*, 📅 *Tgl Rilis*, ⏳ *Durasi*, 🎭 *Genre*, 📝 *Sinopsis (2 kalimat)*. "
                  f"Gunakan gaya pakar film. JANGAN BERTELE-TELE.")
    else:
        prompt = f"Kamu Joni, manusia asli pakar film @SheJua. Sapa Kak {name}. Jawab sangat singkat & gaul: {text}"
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(G_URL, json=payload, timeout=25)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return f"Aduh sob {name}, Joni lagi pening dikit habis maraton film. 🍿"

# --- [ WELCOME MESSAGE ] ---
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(m):
    for user in m.new_chat_members:
        name = user.first_name
        pesan = (f"Halo Kak {name}! Selamat datang di @SheJua 🎬\n\n"
                 f"Kenalin, aku **Joni**, asisten film di sini. Cara panggil aku:\n"
                 f"🔹 Sebut kata **'sob'** di pesanmu.\n"
                 f"🔹 Atau langsung **Reply** pesan aku.\n\n"
                 f"📌 Cek peraturan grup ketik `/rules` ya!")
        bot.reply_to(m, pesan, parse_mode="Markdown")

# --- [ FITUR #REQUEST ] ---
@bot.message_handler(func=lambda m: m.text and m.text.startswith('#request'))
def handle_request(m):
    # Mencari pola: #request [Judul Bebas] [4 Digit Tahun]
    pattern = r"#request\s+(.+)\s+(\d{4})"
    match = re.search(pattern, m.text)
    
    if match:
        judul = match.group(1).strip()
        tahun = match.group(2)
        
        # Kirim Detail ke ID Kamu
        info_req = (f"📌 **REQUEST FILM BARU**\n\n"
                    f"👤 **Dari:** {m.from_user.first_name} (@{m.from_user.username})\n"
                    f"🎬 **Film:** {judul}\n"
                    f"📅 **Tahun:** {tahun}")
        
        try:
            bot.send_message(TARGET_REQUEST_ID, info_req, parse_mode="Markdown")
            bot.reply_to(m, f"✅ Sip Kak {m.from_user.first_name}, request **{judul} ({tahun})** sudah Joni terima dan diteruskan ke Admin! Ditunggu ya. 🥂")
        except:
            bot.reply_to(m, "✅ Request diterima! Tapi Joni gagal lapor ke Saved Messages Admin. Pastikan Admin sudah klik /start di bot ini ya!")
    else:
        bot.reply_to(m, (f"⚠️ **Waduh Sob {m.from_user.first_name}, Salah Format!**\n\n"
                         f"Ketiknya gini ya: `#request Judul Tahun` \n"
                         f"Contoh: `#request Avatar 2009`"))

# --- [ FITUR /IMDB ] ---
@bot.message_handler(commands=['imdb'])
def imdb_info(m):
    query = m.text.replace('/imdb', '').strip()
    if not query:
        bot.reply_to(m, "Kasih judul filmnya dong sob! Contoh: `/imdb Inception`")
        return
    bot.send_chat_action(m.chat.id, 'typing')
    jawaban = joni_brain(query, m.from_user.first_name, is_imdb=True)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("👤 Hubungi Admin", url="https://t.me/filmberbobot"))
    bot.reply_to(m, jawaban, parse_mode="Markdown", reply_markup=markup)

# --- [ CHAT AUTOMATIC ] ---
@bot.message_handler(func=lambda m: True)
def group_chat(m):
    if m.text:
        is_sob = "sob" in m.text.lower()
        is_reply = m.reply_to_message and m.reply_to_message.from_user.id == bot.get_me().id
        if is_sob or is_reply or m.chat.type == 'private':
            bot.send_chat_action(m.chat.id, 'typing')
            jawaban = joni_brain(m.text, m.from_user.first_name)
            bot.reply_to(m, jawaban)

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
    return "Joni @SheJua (Gemini 2.5 Flash) is Online! 🚀", 200

def handler(request):
    return app(request)
