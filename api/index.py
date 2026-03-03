import os, requests, telebot
from flask import Flask, request

# --- [ KONFIGURASI AMAN VERCEL ] ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
G_KEY = os.getenv("GEMINI_API_KEY")

# Menggunakan Jalur Gemini 2.5 Flash yang sukses di CMD tadi
G_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={G_KEY}"

app = Flask(__name__)
# Tambahkan ini agar Vercel tidak bingung mencari aplikasi Flask-nya
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

bot = telebot.TeleBot(TOKEN, threaded=False)

# --- [ FUNGSI OTAK JONI ] ---
def joni_brain(text, name):
    # Prompt khusus agar Joni tetap menjadi manusia asli
    prompt = (
        f"Kamu Joni, manusia asli pakar film di grup @SheJua. JANGAN SEBUT DIRIMU AI/BOT. "
        f"Gunakan gaya bahasa santai dan akrab. Sapa Kak {name}. "
        f"Jawab ini: {text}"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        res = requests.post(G_URL, json=payload, timeout=25)
        res_json = res.json()
        # Ambil hasil dari Gemini 2.5 Flash
        return res_json['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"Error Gemini: {e}")
        return f"Aduh sob {name}, Joni lagi pening dikit habis maraton film. Coba lagi ya! 🍿"

# --- [ ROUTE UTAMA VERCEL ] ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            # Mengolah update dari Telegram
            json_str = request.get_data().decode('UTF-8')
            update = telebot.types.Update.de_json(json_str)
            bot.process_new_updates([update])
            return "OK", 200
        except Exception as e:
            print(f"Error Update: {e}")
            return "Error", 500
    return "Joni @SheJua (Gemini 2.5 Flash) is Online! 🚀", 200

# --- [ FITUR /IMDB ] ---
@bot.message_handler(commands=['imdb'])
def imdb_info(m):
    query = m.text.replace('/imdb', '').strip()
    if not query:
        bot.reply_to(m, "Kasih judul filmnya dong sob! Contoh: `/imdb Inception`")
        return
    bot.send_chat_action(m.chat.id, 'typing')
    jawaban = joni_brain(f"Berikan info lengkap IMDB (rating, tahun, sinopsis) untuk film: {query}", m.from_user.first_name)
    bot.reply_to(m, jawaban)

# --- [ FITUR CHAT ] ---
@bot.message_handler(func=lambda m: True)
def group_chat(m):
    is_sob = m.text and "sob" in m.text.lower()
    is_reply = m.reply_to_message and m.reply_to_message.from_user.id == bot.get_me().id
    if is_sob or is_reply or m.chat.type == 'private':
        bot.send_chat_action(m.chat.id, 'typing')
        jawaban = joni_brain(m.text, m.from_user.first_name)
        bot.reply_to(m, jawaban)

# --- [ MANTRA WAJIB VERCEL ] ---
# Baris ini sangat penting untuk mencegah 'Function Invocation Failed'
application = app
