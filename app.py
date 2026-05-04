from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import yt_dlp
import requests
import os

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'Referer': 'https://www.youtube.com/',
}

def base_ydl_opts():
    return {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'nocheckcertificate': True,
        'http_headers': HEADERS,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
                'skip': ['hls', 'dash'],
            }
        },
    }

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/search')
def search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'error': 'No query'}), 400
    try:
        opts = base_ydl_opts()
        opts['extract_flat'] = True
        with yt_dlp.YoutubeDL(opts) as ydl:
            result = ydl.extract_info(f"ytsearch20:{q}", download=False)
            entries = result.get('entries', []) or []
            items = []
            for e in entries:
                if not e:
                    continue
                vid_id = e.get('id', '')
                if not vid_id:
                    continue
                items.append({
                    'id': vid_id,
                    'title': e.get('title', 'Sin título'),
                    'channel': e.get('uploader') or e.get('channel') or '',
                    'duration': e.get('duration') or 0,
                    'thumb': f"https://i.ytimg.com/vi/{vid_id}/mqdefault.jpg",
                })
            return jsonify({'items': items})
    except Exception as ex:
        return jsonify({'error': str(ex)}), 500

@app.route('/stream/<video_id>')
def stream(video_id):
    try:
        opts = base_ydl_opts()
        opts['format'] = 'bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio/best'

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={video_id}",
                download=False
            )

        formats = info.get('formats', [])
        audio_only = [
            f for f in formats
            if f.get('vcodec') == 'none'
            and f.get('acodec') not in (None, 'none')
            and f.get('url')
        ]
        if not audio_only:
            audio_only = [
                f for f in formats
                if f.get('acodec') not in (None, 'none') and f.get('url')
            ]
        if not audio_only:
            return jsonify({'error': 'No audio stream found'}), 404

        audio_only.sort(key=lambda f: f.get('abr') or f.get('tbr') or 0, reverse=True)
        best = audio_only[0]
        audio_url = best['url']

        ext = best.get('ext', 'webm')
        mime_map = {'webm': 'audio/webm', 'm4a': 'audio/mp4', 'mp4': 'audio/mp4', 'ogg': 'audio/ogg'}
        mime = mime_map.get(ext, 'audio/webm')

        req_headers = dict(HEADERS)
        range_header = request.headers.get('Range')
        if range_header:
            req_headers['Range'] = range_header

        r = requests.get(audio_url, headers=req_headers, stream=True, timeout=30)

        resp_headers = {
            'Content-Type': mime,
            'Accept-Ranges': 'bytes',
            'Access-Control-Allow-Origin': '*',
            'Cache-Control': 'no-cache',
        }
        if 'Content-Length' in r.headers:
            resp_headers['Content-Length'] = r.headers['Content-Length']
        if 'Content-Range' in r.headers:
            resp_headers['Content-Range'] = r.headers['Content-Range']

        return Response(
            r.iter_content(chunk_size=16384),
            status=r.status_code,
            headers=resp_headers,
            content_type=mime,
        )

    except Exception as ex:
        print(f"Stream error for {video_id}: {ex}")
        return jsonify({'error': str(ex)}), 500

@app.route('/ping')
def ping():
    return jsonify({'status': 'ok', 'yt_dlp': yt_dlp.version.__version__})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
