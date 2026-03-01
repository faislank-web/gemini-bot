import os
import telebot
import requests
import google.generativeai as genai
from flask import Flask, request

# Mengambil data dari Variables Zeabur
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
ZEABUR_URL = os.environ.get("ZEABUR_WEB_URL")

# Inisialisasi Gemini dengan model terbaru agar tidak 404
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def getMessage():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    return "Forbidden", 403

@app.route('/')
def setup():
    if not ZEABUR_URL:
        return "<h1>⚠️ Peringatan</h1><p>Mohon set ZEABUR_WEB_URL di tab Variables!</p>", 500
    
    clean_url = ZEABUR_URL.replace("https://", "").replace("http://", "").strip("/")
    webhook_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url=https://{clean_url}/{TELEGRAM_TOKEN}"
    
    resp = requests.get(webhook_url)
    # Sesuai permintaan: Ganti teks suksesnya
    return f"<h1>📍 Upload Complete Selamat Menyaksikan</h1><p>Status: {resp.text}</p>", 200

@bot.message_handler(func=lambda message: True)
def ai_reply(message):
    try:
        # Mengirim teks ke Gemini
        response = model.generate_content(message.text)
        bot.reply_to(message, response.text)
    except Exception as e:
        print(f"Error: {e}")
        # Jika masih error, kita beri tau user dengan halus
        bot.reply_to(message, "Sabar ya, AI-nya lagi tarik napas sebentar... Coba lagi yuk! 🙏")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
