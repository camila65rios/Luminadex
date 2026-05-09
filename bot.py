import os
import re
import time
import base64
import urllib.parse
import threading
import subprocess
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, render_template_string

# ==========================================
# CONFIGURACIÓN Y VARIABLES SEGURAS
# ==========================================
TOKEN = os.environ.get('TOKEN')
SHEET_URL = os.environ.get('SHEET_URL')
WEB_URL = os.environ.get('WEB_URL', 'http://localhost:8080')

if not TOKEN or not SHEET_URL:
    raise ValueError("⚠️ Faltan variables de entorno (TOKEN o SHEET_URL).")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ==========================================
# INTERFAZ WEB (DISEÑO BLANCO Y PROFESIONAL)
# ==========================================
HTML_GALLERY = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Catálogo | Vault</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root { --bg: #f8fafc; --card: #ffffff; --text: #1e293b; --primary: #2563eb; --border: #e2e8f0; }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background-color: var(--bg); color: var(--text); padding-bottom: 2rem; }
        header { background: var(--card); border-bottom: 1px solid var(--border); padding: 1.5rem 2rem; box-shadow: 0 1px 2px rgba(0,0,0,0.03); display: flex; align-items: center; justify-content: space-between; }
        .logo { font-size: 1.25rem; font-weight: 600; letter-spacing: -0.5px; }
        .container { max-width: 1200px; margin: 2rem auto; padding: 0 1.5rem; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; }
        .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; transition: box-shadow 0.2s, transform 0.2s; text-decoration: none; color: inherit; display: block; }
        .card:hover { transform: translateY(-3px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
        .thumbnail { width: 100%; height: 140px; background-color: #e2e8f0; background-size: cover; background-position: center; border-bottom: 1px solid var(--border); }
        .info { padding: 1rem; }
        .title { font-size: 0.95rem; font-weight: 500; margin-bottom: 0.25rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .date { font-size: 0.75rem; color: #64748b; }
        .empty-state { text-align: center; padding: 3rem; color: #64748b; width: 100%; }
    </style>
</head>
<body>
    <header>
        <div class="logo">Lumina Streaming Vault</div>
        <div style="font-size: 0.85rem; color: #64748b;">Entorno Privado</div>
    </header>
    <div class="container">
        <div class="grid">
            {% if videos|length == 0 %}
                <div class="empty-state">No hay videos en la bóveda aún. Añade uno desde Telegram.</div>
            {% else %}
                {% for video in videos|reverse %}
                <a href="/ver/{{ video.ID_Video }}" class="card">
                    <div class="thumbnail" style="background-image: url('{{ video.Portada_Base64 }}');"></div>
                    <div class="info">
                        <div class="title">{{ video.Titulo }}</div>
                        <div class="date">Añadido: {{ video.Fecha }}</div>
                    </div>
                </a>
                {% endfor %}
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

HTML_PLAYER = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reproductor | Vault</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        body { background-color: #f8fafc; font-family: 'Inter', sans-serif; margin: 0; display: flex; flex-direction: column; align-items: center; min-height: 100vh; }
        .nav { width: 100%; padding: 1rem 2rem; background: #ffffff; border-bottom: 1px solid #e2e8f0; margin-bottom: 2rem; }
        .back-btn { text-decoration: none; color: #2563eb; font-weight: 500; font-size: 0.9rem; display: inline-flex; align-items: center; gap: 5px; }
        .back-btn:hover { text-decoration: underline; }
        .player-wrapper { width: 100%; max-width: 900px; padding: 0 1rem; }
        .video-title { font-size: 1.5rem; font-weight: 600; color: #1e293b; margin-bottom: 1rem; }
        video { width: 100%; border-radius: 12px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1); background: #000; outline: none; }
    </style>
</head>
<body>
    <div class="nav">
        <a href="/" class="back-btn">&#8592; Volver al Catálogo</a>
    </div>
    <div class="player-wrapper">
        <div class="video-title">{{ video.Titulo }}</div>
        <video controls controlsList="nodownload">
            <source src="{{ video.Enlace_Mediafire }}" type="video/mp4">
            Tu navegador no soporta la reproducción de video.
        </video>
    </div>
</body>
</html>
"""

# ==========================================
# RUTAS DEL SERVIDOR WEB
# ==========================================
@app.route('/')
def index():
    try:
        resp = requests.get(SHEET_URL)
        data = resp.json().get('data', [])
        return render_template_string(HTML_GALLERY, videos=data)
    except:
        return "Error al conectar con la base de datos."

@app.route('/ver/<video_id>')
def watch(video_id):
    try:
        resp = requests.get(SHEET_URL)
        data = resp.json().get('data', [])
        video = next((v for v in data if str(v['ID_Video']) == str(video_id)), None)
        if video:
            return render_template_string(HTML_PLAYER, video=video)
        return "Video no encontrado.", 404
    except:
        return "Error al cargar el reproductor."

def run_web_server():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web_server, daemon=True).start()

# ==========================================
# LÓGICA DEL BOT DE TELEGRAM
# ==========================================
def send_main_menu(chat_id, text="Panel de Control del Catálogo:"):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🎬 Abrir Catálogo Web", url=WEB_URL),
        InlineKeyboardButton("🔍 Ver Historial Rápido", callback_data="history")
    )
    bot.send_message(chat_id, text, reply_markup=markup)

@bot.message_handler(commands=['start', 'menu'])
def start_command(message):
    send_main_menu(message.chat.id, "Bienvenido a la Bóveda.\nEnvía un enlace de Mediafire Premium para añadirlo automáticamente al catálogo.")

@bot.message_handler(func=lambda m: m.text.startswith('http'))
def process_mediafire_link(message):
    chat_id = message.chat.id
    url = message.text.strip()
    
    if "mediafire.com" not in url:
        bot.reply_to(message, "⚠️ El enlace no parece ser de Mediafire.")
        return

    msg_status = bot.reply_to(message, "⏳ *Procesando enlace...*\nExtrayendo metadatos y miniatura (segundo 35)...", parse_mode="Markdown")

    try:
        # 1. Limpieza Inteligente del Título
        raw_name = url.split('/')[-2] if len(url.split('/')) > 2 else "Video_Sin_Nombre"
        clean_name = urllib.parse.unquote(raw_name)
        clean_name = clean_name.replace('_', ' ').replace('.mp4', '').strip()
        
        # 2. Extracción de Fotograma con FFmpeg (Fuerza Bruta Directa)
        # Se escala a 480p máximo para asegurar que Base64 no sea pesado para Google Sheets
        cmd = [
            'ffmpeg', '-ss', '35', '-i', url, '-vframes', '1', 
            '-q:v', '5', '-vf', 'scale=480:-1', 
            '-f', 'image2', '-c:v', 'mjpeg', 'pipe:1'
        ]
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        out, _ = process.communicate()
        
        if not out:
            # Si falla la extracción, usamos una imagen gris por defecto
            b64_string = ""
        else:
            b64_string = "data:image/jpeg;base64," + base64.b64encode(out).decode('utf-8')
            
        # 3. Empaquetado y Envío a Google Sheets
        video_id = str(int(time.time()))
        payload = {
            "id": video_id,
            "titulo": clean_name,
            "enlace": url,
            "portada": b64_string,
            "fecha": time.strftime("%d/%m/%Y")
        }
        
        response = requests.post(SHEET_URL, json=payload)
        
        if response.status_code == 200:
            bot.delete_message(chat_id, msg_status.message_id)
            bot.send_message(
                chat_id, 
                f"✅ *Video Guardado Exitosamente*\n\n📄 *Título:* `{clean_name}`", 
                parse_mode="Markdown"
            )
            send_main_menu(chat_id, "¿Qué deseas hacer ahora?")
        else:
            bot.edit_message_text("❌ Error al guardar en la base de datos.", chat_id=chat_id, message_id=msg_status.message_id)

    except Exception as e:
        error_str = str(e).replace('_', '\\_')
        bot.edit_message_text(f"❌ *Error interno:*\n`{error_str}`", chat_id=chat_id, message_id=msg_status.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "history")
def show_history(call):
    chat_id = call.message.chat.id
    bot.edit_message_text("⏳ Consultando la Bóveda...", chat_id=chat_id, message_id=call.message.message_id)
    
    try:
        resp = requests.get(SHEET_URL)
        data = resp.json().get('data', [])
        
        if not data:
            bot.edit_message_text("📭 La bóveda está vacía.", chat_id=chat_id, message_id=call.message.message_id)
            send_main_menu(chat_id)
            return
            
        markup = InlineKeyboardMarkup(row_width=1)
        # Mostramos los últimos 5 para no saturar el chat de Telegram
        for video in reversed(data[-5:]):
            url_reproductor = f"{WEB_URL}/ver/{video['ID_Video']}"
            markup.add(InlineKeyboardButton(f"▶️ {video['Titulo']}", url=url_reproductor))
            
        markup.add(InlineKeyboardButton("🔙 Volver al Menú", callback_data="menu"))
        bot.edit_message_text("📋 *Últimos 5 videos guardados:*", chat_id=chat_id, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        
    except Exception as e:
        bot.edit_message_text("❌ Error al leer el catálogo.", chat_id=chat_id, message_id=call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "menu")
def return_menu(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    send_main_menu(call.message.chat.id)

print("🚀 Lumina Streaming Vault Iniciado...")
bot.infinity_polling()
