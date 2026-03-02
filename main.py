import os
import requests
import telebot
from telebot import types
from flask import Flask, request

# --- [ DATA AKSES ] ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
ZEABUR_URL = os.environ.get("ZEABUR_WEB_URL")
TMDB_KEY = "61e2290429798c561450eb56b26de19b"

# --- [ URL MODEL ] ---
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"

SYS_INSTRUCT = (
    "Kamu adalah Joni, manusia asli pakar film yang asik. "
    "Bicaralah seperti teman akrab dengan banyak emotikon. "
    "Jangan bilang kamu AI atau bot. Di chat personal langsung jawab santai. "
    "Di grup panggil 'sob' kalau di-reply."
)

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# --- [ TOMBOL NAVIGASI ] ---
def movie_buttons():
    markup = types.InlineKeyboardMarkup()
    # Menambahkan tombol Nonton sesuai request Kakak
    btn_nonton = types.InlineKeyboardButton("🎬 Nonton Disini", url="https://t.me/SheJua")
    btn_admin = types.InlineKeyboardButton("☎️ Chat Admin", url="https://t.me/filmberbobot")
    markup.add(btn_nonton)
    markup.add(btn_admin)
    return markup

def get_gemini_response(user_text):
    payload = {"contents": [{"parts": [{"text": f"{SYS_INSTRUCT}\n\nPertanyaan user: {user_text}"}]}]}
    try:
        response = requests.post(GEMINI_URL, json=payload)
        data = response.json()
        if 'candidates' in data and data['candidates']:
            return data['candidates'][0]['content']['parts'][0]['text']
        return None
    except: return None

# --- [ FUNGSI TMDB LENGKAP ] ---
def get_tmdb_detail(m_id, u_name):
    url = f"https://api.themoviedb.org/3/movie/{m_id}?api_key={TMDB_KEY}&language=id-ID&append_to_response=credits"
    try:
        res = requests.get(url).json()
        title = res.get('title', 'Unknown').upper()
        release_date = res.get('release_date', '????-??-??')
        year = release_date[:4]
        runtime = res.get('runtime', 0)
        
        rating = res.get('vote_average', 0)
        stars = "⭐" * int(rating/2) if rating > 0 else "🌑"
        genres = ", ".join([g['name'] for g in res.get('genres', [])])
        cast = ", ".join([c['name'] for c in res.get('credits', {}).get('cast', [])[:3]])
        plot = res.get('overview', 'Sinopsis belum tersedia.')
        p_url = f"https://image.tmdb.org/t/p/w500{res.get('poster_path')}" if res.get('poster_path') else None

        caption = (
            f"🎬 **{title}** ({year})\n"
            f"--------------------------------------\n\n"
            f"📅 **Rilis** : {release_date}\n"
            f"⏳ **Durasi** : {runtime} Menit\n"
            f"🌟 **Rating** : {rating:.1f}/10 {stars}\n"
            f"🎭 **Genre** : {genres}\n"
            f"👥 **Cast** : {cast}\n\n"
            f"📖 **SINOPSIS** :\n"
            f"{plot[:500] + '...' if len(plot) > 500 else plot}\n\n"
            f"--------------------------------------\n"
            f"👤 User: Kak {u_name}"
        )
        return
