import os
import logging
from flask import Flask, render_template, request, jsonify, send_file, after_this_request
import yt_dlp
from urllib.parse import urlparse
import tempfile
import shutil
import re
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET')
if not app.secret_key:
    logger.warning("SESSION_SECRET not set, generating random key for development")
    app.secret_key = os.urandom(24).hex()

def is_valid_youtube_url(url):
    """Validate if the given URL is a YouTube URL"""
    try:
        parsed = urlparse(url)
        return 'youtube.com' in parsed.netloc or 'youtu.be' in parsed.netloc
    except:
        return False

def sanitize_filename(filename):
    """Sanitize filename to be safe for all filesystems"""
    if not filename:
        return "download"
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = re.sub(r'\s+', ' ', filename)
    if len(filename) > 200:
        filename = filename[:200]
    return filename.strip()

def get_exact_browser_headers():
    """EXACTAMENTE los mismos headers que tu navegador Chrome"""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9,es;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Sec-CH-UA': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        'Sec-CH-UA-Arch': '"x86"',
        'Sec-CH-UA-Bitness': '"64"',
        'Sec-CH-UA-Full-Version': '"141.0.7390.65"',
        'Sec-CH-UA-Full-Version-List': '"Google Chrome";v="141.0.7390.65", "Not?A_Brand";v="8.0.0.0", "Chromium";v="141.0.7390.65"',
        'Sec-CH-UA-Mobile': '?0',
        'Sec-CH-UA-Model': '""',
        'Sec-CH-UA-Platform': '"Windows"',
        'Sec-CH-UA-Platform-Version': '"19.0.0"',
        'Sec-CH-UA-Wow64': '?0',
        'Sec-CH-UA-Form-Factors': '"Desktop"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Referer': 'https://www.youtube.com/',
        'Origin': 'https://www.youtube.com',
    }

def search_youtube(query, max_results=5):
    """Search YouTube for videos with multiple fallback strategies"""
    
    # Strategy 1: Try with cookies and browser headers
    try:
        cookie_path = None
        for path in ['cookies.txt', 'youtube_cookies.txt']:
            if os.path.exists(path):
                cookie_path = path
                break
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
            'http_headers': get_exact_browser_headers(),
            'extractor_args': {'youtube': {'skip': ['hls', 'dash']}},
        }
        
        if cookie_path:
            ydl_opts['cookiefile'] = cookie_path
            logger.info(f"🍪 Using cookies for search: {cookie_path}")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if is_valid_youtube_url(query):
                info = ydl.extract_info(query, download=False)
                if info:
                    return [info]
            else:
                results = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
                if results and 'entries' in results:
                    return results['entries']
        
    except Exception as e:
        logger.warning(f"Search strategy 1 failed: {str(e)}")
    
    # Strategy 2: Try with minimal options
    try:
        logger.info("Trying search with minimal options")
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
            if results and 'entries' in results:
                # Extract full info for each result
                videos = []
                for entry in results['entries']:
                    if entry and entry.get('id'):
                        try:
                            video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                            video_info = ydl.extract_info(video_url, download=False)
                            if video_info:
                                videos.append(video_info)
                        except:
                            continue
                if videos:
                    return videos
    except Exception as e:
        logger.warning(f"Search strategy 2 failed: {str(e)}")
    
    logger.error("All search strategies failed")
    return []

def download_with_real_browser_headers(video_url, temp_dir, format_type='mp4'):
    """Descarga usando EXACTAMENTE los mismos headers del navegador"""
    
    # ESTRATEGIA 1: Headers exactos del navegador
    try:
        logger.info("🎯 Estrategia 1: Headers exactos de Chrome")
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'http_headers': get_exact_browser_headers(),
            'retries': 5,
            'fragment_retries': 5,
        }
        
        if format_type == 'mp3':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'keepvideo': False,
            })
        else:
            ydl_opts.update({
                'format': 'best[height<=720]/best[ext=mp4]/best',
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'merge_output_format': 'mp4',
            })
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            
            # Buscar archivo descargado
            extensions = ['.mp3', '.m4a'] if format_type == 'mp3' else ['.mp4', '.mkv', '.webm']
            for file in os.listdir(temp_dir):
                if any(file.endswith(ext) for ext in extensions):
                    filename = os.path.join(temp_dir, file)
                    safe_title = sanitize_filename(info.get('title', 'download') if info else 'download')
                    
                    if format_type == 'mp3':
                        download_name = f"{safe_title}.mp3"
                    else:
                        download_name = f"{safe_title}.mp4"
                    
                    logger.info(f"✅ ÉXITO Estrategia 1: {download_name}")
                    return filename, download_name
    except Exception as e:
        logger.warning(f"Estrategia 1 falló: {str(e)}")
    
    # ESTRATEGIA 2: Con cookies + headers reales
    try:
        logger.info("🎯 Estrategia 2: Cookies + Headers reales")
        
        # Buscar cookies
        cookie_path = None
        for path in ['cookies.txt', 'youtube_cookies.txt']:
            if os.path.exists(path):
                cookie_path = path
                break
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'http_headers': get_exact_browser_headers(),
            'retries': 3,
        }
        
        if cookie_path:
            ydl_opts['cookiefile'] = cookie_path
            logger.info(f"🍪 Usando cookies: {cookie_path}")
        
        if format_type == 'mp3':
            ydl_opts.update({
                'format': 'bestaudio[ext=m4a]',
                'outtmpl': os.path.join(temp_dir, 'audio.%(ext)s'),
            })
        else:
            ydl_opts.update({
                'format': 'worst[height>=240]',
                'outtmpl': os.path.join(temp_dir, 'video.%(ext)s'),
            })
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            
            for file in os.listdir(temp_dir):
                if file not in ['.', '..']:
                    filename = os.path.join(temp_dir, file)
                    safe_title = sanitize_filename(info.get('title', 'download') if info else 'download')
                    
                    if format_type == 'mp3':
                        # Convertir m4a a mp3 si es necesario
                        if filename.endswith('.m4a'):
                            import subprocess
                            mp3_file = os.path.join(temp_dir, f"{safe_title}.mp3")
                            try:
                                subprocess.run([
                                    'ffmpeg', '-i', filename, '-codec:a', 'libmp3lame',
                                    '-q:a', '2', mp3_file, '-y', '-hide_banner', '-loglevel', 'error'
                                ], capture_output=True, timeout=30)
                                if os.path.exists(mp3_file):
                                    os.remove(filename)
                                    filename = mp3_file
                            except:
                                pass
                        download_name = f"{safe_title}.mp3"
                    else:
                        download_name = f"{safe_title}.mp4"
                    
                    logger.info(f"✅ ÉXITO Estrategia 2: {download_name}")
                    return filename, download_name
    except Exception as e:
        logger.warning(f"Estrategia 2 falló: {str(e)}")
    
    # ESTRATEGIA 3: Comando directo con user-agent real
    try:
        logger.info("🎯 Estrategia 3: Comando directo")
        
        user_agent = get_exact_browser_headers()['User-Agent']
        
        if format_type == 'mp3':
            cmd = f'yt-dlp --user-agent "{user_agent}" -x --audio-format mp3 --audio-quality 2 -o "{temp_dir}/output.%(ext)s" "{video_url}"'
        else:
            cmd = f'yt-dlp --user-agent "{user_agent}" -f "best[height<=480]" -o "{temp_dir}/output.%(ext)s" "{video_url}"'
        
        result = os.system(cmd)
        
        if result == 0:  # Comando exitoso
            for file in os.listdir(temp_dir):
                if file not in ['.', '..']:
                    filename = os.path.join(temp_dir, file)
                    
                    # Obtener título del video
                    try:
                        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                            info = ydl.extract_info(video_url, download=False)
                            safe_title = sanitize_filename(info.get('title', 'download') if info else 'download')
                    except:
                        safe_title = 'download'
                    
                    if format_type == 'mp3':
                        download_name = f"{safe_title}.mp3"
                    else:
                        download_name = f"{safe_title}.mp4"
                    
                    logger.info(f"✅ ÉXITO Estrategia 3: {download_name}")
                    return filename, download_name
    except Exception as e:
        logger.warning(f"Estrategia 3 falló: {str(e)}")
    
    raise Exception("Todas las estrategias fallaron. YouTube está bloqueando las descargas.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query', '')
    if not query:
        return jsonify({'error': 'No search query provided'}), 400

    results = search_youtube(query)
    formatted_results = []

    for result in results:
        if result:
            duration = result.get('duration', 0)
            if duration:
                duration_str = f"{int(duration // 60)}:{int(duration % 60):02d}"
            else:
                duration_str = "N/A"
                
            formatted_result = {
                'title': result.get('title', ''),
                'url': result.get('webpage_url', result.get('url', '')),
                'uploader': result.get('uploader', 'Unknown'),
                'duration': duration_str,
                'view_count': result.get('view_count', 0),
                'description': result.get('description', '')[:200] + '...' if result.get('description') else '',
                'upload_date': result.get('upload_date', ''),
                'thumbnail': result.get('thumbnail', ''),
            }
            formatted_results.append(formatted_result)

    return jsonify({'results': formatted_results})

@app.route('/download', methods=['POST'])
def download():
    video_url = request.form.get('url')
    format_type = request.form.get('format', 'mp3')

    if not video_url:
        return jsonify({'error': 'No URL provided'}), 400

    if not is_valid_youtube_url(video_url):
        return jsonify({'error': 'Invalid YouTube URL provided'}), 400

    logger.info(f"🚀 INICIANDO DESCARGA CON HEADERS REALES: {video_url}")

    temp_dir = tempfile.mkdtemp()
    try:
        filename, download_name = download_with_real_browser_headers(video_url, temp_dir, format_type)

        @after_this_request
        def cleanup(response):
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception as e:
                logger.error(f"Error cleaning up temp directory: {str(e)}")
            return response

        mime_type = 'audio/mpeg' if format_type == 'mp3' else 'video/mp4'
        
        logger.info(f"🎉 DESCARGA EXITOSA: {download_name}")
        return send_file(
            filename,
            as_attachment=True,
            download_name=download_name,
            mimetype=mime_type
        )

    except Exception as e:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        error_msg = str(e)
        logger.error(f"💥 ERROR: {error_msg}")
        
        return jsonify({'error': f'No se pudo descargar: {error_msg}'}), 500

# API Endpoints
@app.route('/api/download/video', methods=['GET'])
def api_download_video():
    video_url = request.args.get('url')
    
    if not video_url:
        return jsonify({'error': 'No URL provided. Use ?url=YOUTUBE_URL'}), 400
    
    if not is_valid_youtube_url(video_url):
        return jsonify({'error': 'Invalid YouTube URL'}), 400
    
    temp_dir = tempfile.mkdtemp()
    try:
        filename, download_name = download_with_real_browser_headers(video_url, temp_dir, 'mp4')
        
        @after_this_request
        def cleanup(response):
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception as e:
                logger.error(f"Error cleaning up temp directory: {str(e)}")
            return response
        
        return send_file(
            filename,
            as_attachment=True,
            download_name=download_name,
            mimetype='video/mp4'
        )
    except Exception as e:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/audio', methods=['GET'])
def api_download_audio():
    video_url = request.args.get('url')
    
    if not video_url:
        return jsonify({'error': 'No URL provided. Use ?url=YOUTUBE_URL'}), 400
    
    if not is_valid_youtube_url(video_url):
        return jsonify({'error': 'Invalid YouTube URL'}), 400
    
    temp_dir = tempfile.mkdtemp()
    try:
        filename, download_name = download_with_real_browser_headers(video_url, temp_dir, 'mp3')
        
        @after_this_request
        def cleanup(response):
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception as e:
                logger.error(f"Error cleaning up temp directory: {str(e)}")
            return response
        
        return send_file(
            filename,
            as_attachment=True,
            download_name=download_name,
            mimetype='audio/mpeg'
        )
    except Exception as e:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def api_status():
    status_info = {
        'status': 'RUNNING',
        'method': 'HEADERS REALES DE CHROME 141',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
        'message': '✅ Usando headers exactos del navegador'
    }
    
    return jsonify(status_info)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
