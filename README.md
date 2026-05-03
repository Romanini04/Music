# MúsicaApp 🎵

App de música que busca y reproduce audio de YouTube usando yt-dlp.

## Archivos
- `app.py` — Backend Flask
- `requirements.txt` — Dependencias Python
- `Procfile` — Comando de inicio para Render
- `static/index.html` — Frontend (se sirve desde el backend)

## Cómo subir a Render (paso a paso)

### 1. Sube a GitHub
1. Ve a github.com y crea un repositorio nuevo (ej: `musicapp`)
2. Sube estos 4 archivos:
   - `app.py`
   - `requirements.txt`
   - `Procfile`
   - `static/index.html` (dentro de una carpeta llamada `static`)

### 2. Conecta con Render
1. Ve a **render.com** e inicia sesión con GitHub
2. Click en **"New +"** → **"Web Service"**
3. Selecciona tu repositorio `musicapp`
4. Configuración:
   - **Name:** musicapp (o el nombre que quieras)
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --workers 2 --timeout 120`
5. Click **"Create Web Service"**
6. Espera 3-5 minutos mientras hace el deploy

### 3. Usa la app
1. Render te dará una URL tipo `https://musicapp-xxxx.onrender.com`
2. Abre esa URL en tu celular
3. ¡Busca y escucha música! 🎵

## Notas
- El servidor "duerme" tras 15 min sin uso (plan gratis)
- La primera carga después del sueño tarda ~30 segundos
- No hay límite de búsquedas
