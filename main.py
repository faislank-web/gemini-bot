import os
import sys
import threading
import subprocess
import requests
import telebot
from telebot import types
import google.generativeai as genai
from flask import Flask, request

# --- [ DATA AKSES ] ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
ZEABUR_URL = os.environ.get("ZEABUR_WEB_URL")
CHAT_ID = -1003588375021 

# Inisialisasi AI
genai.configure(api_key=GEMINI_KEY)
instruction = "Kamu pakar film IMDB. Berikan informasi rating dan sinopsis. Jangan awali dengan kata 'Halo'. Jawab dengan cerdas dan panggil 'sob'."
model_ai = genai.GenerativeModel('gemini-1.5-flash', system_instruction=instruction)

# Kamus sesi chat tiap user
user_sessions = {}

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# --- [ FUNGSI TOMBOL ADMIN ] ---
def admin_button():
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("Hubungi Admin", url="https://t.me/filmberbobot")
    markup.add(btn)
    return markup

def get_user_name(message):
    name = message.from_user.first_name
    return name if name else message.from_user.username

def is_reply_to_bot(message):
    if message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id:
        return True
    return False

# --- [ HANDLER AI: PRIVATE SESSION ] ---
@bot.message_handler(func=lambda m: True)
def filter_ai_reply(message):
    teks = message.text.lower() if message.text else ""
    user_id = message.from_user.id
    user_name = get_user_name(message)
    
    if "sob" in teks and is_reply_to_bot(message):
        try:
            if user_id not in user_sessions:
                user_sessions[user_id] = model_ai.start_chat(history=[])
            
            chat_session = user_sessions[user_id]
            response = chat_session.send_message(message.text)
            
            final_reply = f"Kak {user_name}, {response.text}"
            bot.reply_to(message, final_reply, reply_markup=admin_button())
        except:
            bot.reply_to(message, f"Lagi pening nih Kak {user_name}, nanti ya sob!", reply_markup=admin_button())

# --- [ FITUR /IMDB: DENGAN TOMBOL ] ---
@bot.message_handler(commands=['imdb'])
def search_imdb(message):
    user_name = get_user_name(message)
    query = message.text.split(' ', 1)[1] if len(message.text.split(' ')) > 1 else None
    if not query:
        bot.reply_to(message, f"Kak {user_name}, contohnya begini: /imdb Avatar", reply_markup=admin_button())
        return
    
    prompt = f"Daftar 3-5 film mirip '{query}' dengan tahun dan rating IMDB."
    try:
        response = model_ai.generate_content(prompt)
        text = f"🎬 **Kak {user_name}, ini hasil IMDB untuk '{query}':**\n\n{response.text}"
        bot.reply_to(message, text, reply_markup=admin_button())
    except:
        bot.reply_to(message, f"Database film lagi sibuk, Kak {user_name}!", reply_markup=admin_button())

# --- [ FITUR /AMBIL: VIDEO + WATERMARK 30s ] ---
def download_dan_proses(video_url, message):
    user_name = get_user_name(message)
    save_name = "Psycho_Killer_2026"
    input_vid = f"{save_name}.mp4"
    poster_name = f"{save_name}_poster.jpg"
    output_vid = f"Final_{save_name}.mp4"

    try:
        bot.reply_to(message, f"🎬 Kak {user_name}, video sedang diproses...")
        subprocess.run(['curl', '-L', '-A', 'Mozilla/5.0', '-o', input_vid, video_url], check=True)
        subprocess.run(['ffmpeg', '-ss', '00:00:05', '-i', input_vid, '-frames:v', '1', '-q:v', '2', poster_name, '-y'], capture_output=True)

        # Watermark simpanan: Channel @SheJua & SHEZAN PANGWA (30 Detik Pertama)
        vf = ("drawtext=text='Channel @SheJua':fontcolor=white@0.5:fontsize=28:shadowcolor=black:shadowx=2:shadowy=2:x=(w-tw)/2:y=h-th-65:enable='between(t,0,30)', "
              "drawtext=text='SHEZAN PANGWA':fontcolor=white@0.5:fontsize=28:shadowcolor=black:shadowx=2:shadowy=2:x=(w-tw)/2:y=h-th-25:enable='between(t,0,30)'")
        
        subprocess.run(['ffmpeg', '-i', input_vid, '-vf', vf, '-c:v', 'libx264', '-preset', 'ultrafast', '-c:a', 'copy', output_vid, '-y'], check=True)

        with open(output_vid, 'rb') as video, open(poster_name, 'rb') as photo:
            bot.send_document(
                CHAT_ID, video, 
                thumb=photo, 
                caption=f"📍 **Upload Complete Selamat Menyaksikan Kak {user_name}**",
                reply_markup=admin_button()
            )
        bot.reply_to(message, f"✅ 📍 **Upload Complete Selamat Menyaksikan Kak {user_name}**", reply_markup=admin_button())
    except Exception as e:
        bot.reply_to(message, f"❌ Gagal Kak {user_name}: {str(e)}", reply_markup=admin_button())
    finally:
        for f in [input_vid, output_vid, poster_name]:
            if os.path.exists(f): os.remove(f)

@bot.message_handler(commands=['ambil'])
def handle_ambil(message):
    url = message.text.split(' ')[1] if len(message.text.split(' ')) > 1 else None
    if url: threading.Thread(target=download_dan_proses, args=(url, message)).start()
    else: bot.reply_to(message, "Gunakan format: /ambil [URL]")

# --- [ ROUTE FLASK / WEBHOOK ] ---
@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def get_message():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    return "Forbidden", 403

@app.route('/')
def setup():
    if not ZEABUR_
