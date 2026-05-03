from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import yt_dlp
import requests

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

def get_ydl_opts():
    return {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'skip_download': True,
    }

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/search')
def search():
    q = request.args.get('q', '')
    if not q:
        return jsonify({'error': 'No query'}), 400

    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'skip_download': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f"ytsearch20:{q}", download=False)
            entries = result.get('entries', [])
            items = []
            for e in entries:
                if not e:
                    continue
                vid_id = e.get('id', '')
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
        ydl_opts = get_ydl_opts()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            
            # Get best audio URL
            formats = info.get('formats', [])
            audio_formats = [f for f in formats if f.get('vcodec') == 'none' and f.get('acodec') != 'none' and f.get('url')]
            
            if not audio_formats:
                # Fallback to any format with audio
                audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('url')]
            
            if not audio_formats:
                return jsonify({'error': 'No audio stream found'}), 404
            
            # Sort by quality
            audio_formats.sort(key=lambda f: f.get('abr') or 0, reverse=True)
            best = audio_formats[0]
            
            audio_url = best.get('url')
            content_type = best.get('ext', 'webm')
            mime = f'audio/{content_type}' if content_type in ['webm','mp4','m4a','ogg'] else 'audio/webm'

            # Proxy the audio stream to avoid CORS on the audio URL
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.youtube.com/',
            }
            
            range_header = request.headers.get('Range')
            req_headers = dict(headers)
            if range_header:
                req_headers['Range'] = range_header

            r = requests.get(audio_url, headers=req_headers, stream=True, timeout=30)
            
            status = r.status_code
            resp_headers = {
                'Content-Type': mime,
                'Accept-Ranges': 'bytes',
                'Access-Control-Allow-Origin': '*',
            }
            if 'Content-Length' in r.headers:
                resp_headers['Content-Length'] = r.headers['Content-Length']
            if 'Content-Range' in r.headers:
                resp_headers['Content-Range'] = r.headers['Content-Range']

            return Response(
                r.iter_content(chunk_size=8192),
                status=status,
                headers=resp_headers,
                content_type=mime,
            )

    except Exception as ex:
        return jsonify({'error': str(ex)}), 500

@app.route('/info/<video_id>')
def info(video_id):
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            return jsonify({
                'id': video_id,
                'title': info.get('title',''),
                'channel': info.get('uploader') or info.get('channel') or '',
                'duration': info.get('duration') or 0,
                'thumb': info.get('thumbnail') or f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg",
            })
    except Exception as ex:
        return jsonify({'error': str(ex)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
