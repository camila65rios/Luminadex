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
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root { --bg: #f8fafc; --card: #ffffff; --text: #0f172a; --muted: #64748b; --border: #e2e8f0; --primary: #2563eb; }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background-color: var(--bg); color: var(--text); padding-bottom: 3rem; -webkit-font-smoothing: antialiased; }
        
        header { background: var(--card); border-bottom: 1px solid var(--border); padding: 1.2rem 2rem; position: sticky; top: 0; z-index: 50; box-shadow: 0 1px 3px rgba(0,0,0,0.05); display: flex; justify-content: space-between; align-items: center; }
        .logo { font-size: 1.2rem; font-weight: 700; color: var(--text); display: flex; align-items: center; gap: 8px; }
        .badge { background: #eff6ff; color: var(--primary); padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; border: 1px solid #bfdbfe; }
        
        .container { max-width: 1200px; margin: 2.5rem auto; padding: 0 1.5rem; }
        .section-title { font-size: 1.5rem; font-weight: 600; margin-bottom: 1.5rem; color: var(--text); }
        
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 24px; }
        .card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; transition: all 0.3s ease; text-decoration: none; color: inherit; display: flex; flex-direction: column; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
        .card:hover { transform: translateY(-4px); box-shadow: 0 12px 20px -8px rgba(0,0,0,0.15); border-color: #cbd5e1; }
        
        .thumbnail { width: 100%; aspect-ratio: 16/9; background-color: #f1f5f9; background-size: cover; background-position: center; border-bottom: 1px solid var(--border); position: relative; }
        .play-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.1); display: flex; justify-content: center; align-items: center; opacity: 0; transition: opacity 0.2s; }
        .card:hover .play-overlay { opacity: 1; }
        .play-icon { width: 48px; height: 48px; background: rgba(255,255,255,0.9); border-radius: 50%; display: flex; justify-content: center; align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        
        .info { padding: 1.2rem; flex-grow: 1; display: flex; flex-direction: column; justify-content: space-between; }
        .title { font-size: 1rem; font-weight: 600; line-height: 1.4; margin-bottom: 0.5rem; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
        .date { font-size: 0.8rem; color: var(--muted); display: flex; align-items: center; gap: 4px; }
        
        .empty-state { grid-column: 1 / -1; text-align: center; padding: 4rem 2rem; background: var(--card); border: 1px dashed #cbd5e1; border-radius: 12px; color: var(--muted); }
    </style>
</head>
<body>
    <header>
        <div class="logo">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"></rect><line x1="7" y1="2" x2="7" y2="22"></line><line x1="17" y1="2" x2="17" y2="22"></line><line x1="2" y1="12" x2="22" y2="12"></line><line x1="2" y1="7" x2="7" y2="7"></line><line x1="2" y1="17" x2="7" y2="17"></line><line x1="17" y1="17" x2="22" y2="17"></line><line x1="17" y1="7" x2="22" y2="7"></line></svg>
            Lumina Vault
        </div>
        <div class="badge">Conexión Segura</div>
    </header>
    <div class="container">
        <h1 class="section-title">Tu Bóveda Multimedia</h1>
        <div class="grid">
            {% if videos|length == 0 %}
                <div class="empty-state">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1.5" style="margin-bottom: 1rem;"><rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"></rect><line x1="7" y1="2" x2="7" y2="22"></line><line x1="17" y1="2" x2="17" y2="22"></line><line x1="2" y1="12" x2="22" y2="12"></line></svg>
                    <h3>No hay videos registrados</h3>
                    <p style="margin-top: 0.5rem; font-size: 0.9rem;">Los enlaces que envíes desde Telegram aparecerán aquí.</p>
                </div>
            {% else %}
                {% for video in videos|reverse %}
                <a href="/ver/{{ video.ID_Video }}" class="card">
                    <div class="thumbnail" style="background-image: url('{{ video.Portada_Base64 }}');">
                        <div class="play-overlay">
                            <div class="play-icon">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="var(--primary)" stroke="var(--primary)" stroke-width="2" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                            </div>
                        </div>
                    </div>
                    <div class="info">
                        <div class="title">{{ video.Titulo }}</div>
                        <div class="date">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                            {{ video.Fecha }}
                        </div>
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
    <title>Reproduciendo: {{ video.Titulo }}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root { --bg: #f8fafc; --card: #ffffff; --text: #0f172a; --border: #e2e8f0; }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background-color: var(--bg); display: flex; flex-direction: column; min-height: 100vh; }
        
        .nav-bar { width: 100%; padding: 1.2rem 2rem; background: var(--card); border-bottom: 1px solid var(--border); box-shadow: 0 1px 2px rgba(0,0,0,0.02); display: flex; align-items: center; position: sticky; top: 0; z-index: 10; }
        .btn-volver { display: inline-flex; align-items: center; gap: 8px; padding: 8px 16px; background: #f1f5f9; color: #334155; border-radius: 8px; text-decoration: none; font-weight: 500; font-size: 0.9rem; transition: all 0.2s; border: 1px solid var(--border); }
        .btn-volver:hover { background: #e2e8f0; color: #0f172a; }
        
        .main-content { flex-grow: 1; display: flex; flex-direction: column; align-items: center; padding: 2rem 1rem; width: 100%; max-width: 1000px; margin: 0 auto; }
        
        .video-header { width: 100%; margin-bottom: 1rem; }
        .video-title { font-size: 1.4rem; font-weight: 600; color: var(--text); line-height: 1.3; }
        .video-meta { font-size: 0.85rem; color: #64748b; margin-top: 0.4rem; }
        
        .video-container { width: 100%; background: #000; border-radius: 12px; overflow: hidden; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04); border: 1px solid #334155; display: flex; justify-content: center; align-items: center; }
        
        video { width: 100%; max-height: 75vh; outline: none; display: block; object-fit: contain; }
        
        @media (max-width: 600px) {
            .nav-bar { padding: 1rem; }
            .main-content { padding: 1.5rem 0.5rem; }
            .video-container { border-radius: 8px; }
            .video-title { font-size: 1.2rem; }
        }
    </style>
</head>
<body>
    <div class="nav-bar">
        <a href="/" class="btn-volver">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
            Catálogo
        </a>
    </div>
    
    <div class="main-content">
        <div class="video-header">
            <h1 class="video-title">{{ video.Titulo }}</h1>
            <div class="video-meta">Agregado el {{ video.Fecha }} • Entorno Privado</div>
        </div>
        
        <div class="video-container">
            <video controls controlsList="nodownload" preload="metadata">
                <source src="{{ video.Enlace_Mediafire }}" type="video/mp4">
                Tu navegador no soporta la reproducción de video.
            </video>
        </div>
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
        return "<div style='padding:2rem; font-family:sans-serif;'>Error al conectar con la base de datos segura.</div>"

@app.route('/ver/<video_id>')
def watch(video_id):
    try:
        resp = requests.get(SHEET_URL)
        data = resp.json().get('data', [])
        video = next((v for v in data if str(v['ID_Video']) == str(video_id)), None)
        if video:
            return render_template_string(HTML_PLAYER, video=video)
        return "<div style='padding:2rem; font-family:sans-serif;'>Video no encontrado en la bóveda.</div>", 404
    except:
        return "<div style='padding:2rem; font-family:sans-serif;'>Error al cargar el reproductor.</div>"

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
    send_main_menu(message.chat.id, "Bienvenido a la Bóveda Lumina.\nEnvía un enlace de Mediafire Premium para añadirlo automáticamente al catálogo.")

@bot.message_handler(func=lambda m: m.text.startswith('http'))
def process_mediafire_link(message):
    chat_id = message.chat.id
    url = message.text.strip()
    
    if "mediafire.com" not in url:
        bot.reply_to(message, "⚠️ El enlace no parece ser de Mediafire.")
        return

    msg_status = bot.reply_to(message, "⏳ *Procesando enlace...*\nLimpiando título y extrayendo miniatura...", parse_mode="Markdown")

    try:
        # 1. Limpieza Inteligente y Estricta del Título (DOBLE DECODIFICACIÓN Y REGEX)
        raw_name = url.split('/')[-2] if len(url.split('/')) > 2 else "Video_Sin_Nombre"
        
        # Descodificar doble vez para limpiar códigos como %2523 -> %23 -> #
        decoded_name = urllib.parse.unquote(urllib.parse.unquote(raw_name))
        
        # Remover la extensión si existe
        decoded_name = decoded_name.replace('.mp4', '').replace('.mkv', '').replace('.avi', '')
        
        # Expresión Regular: Mantener solo letras, números y espacios (elimina #, símbolos, emojis)
        clean_name = re.sub(r'[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s]', ' ', decoded_name)
        
        # Eliminar espacios múltiples que hayan quedado
        clean_name = re.sub(r'\s+', ' ', clean_name).strip()
        
        if not clean_name:
            clean_name = "Video Guardado" # Fallback por si el título era solo símbolos
        
        # 2. Extracción de Fotograma con FFmpeg
        cmd = [
            'ffmpeg', '-ss', '35', '-i', url, '-vframes', '1', 
            '-q:v', '5', '-vf', 'scale=480:-1', 
            '-f', 'image2', '-c:v', 'mjpeg', 'pipe:1'
        ]
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        out, _ = process.communicate()
        
        if not out:
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
