import subprocess
import sys
import os


def startup():
    print("\n╔══════════════════════════════════════╗")
    print("║      Project Phoenix Starting        ║")
    print("╚══════════════════════════════════════╝\n")
    subprocess.run(
        ['apt-get', 'install', '-y', 'ffmpeg'],
        capture_output=True
    )
    pkgs = ['flask', 'requests', 'edge-tts', 'Pillow']
    for p in pkgs:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-q', p],
            capture_output=True
        )
    os.makedirs('output/videos', exist_ok=True)
    os.makedirs('temp', exist_ok=True)
    r = subprocess.run(
        ['ffmpeg', '-version'], capture_output=True
    )
    status = 'ready' if r.returncode == 0 else 'NOT FOUND'
    print(f"FFmpeg: {status}")
    print("Phoenix ready at http://localhost:5000\n")


startup()

from flask import (
    Flask, render_template, request,
    jsonify, send_file
)
import json
import threading
import zipfile
import io
import requests as req
from datetime import datetime

app = Flask(__name__)
current_pipeline = None


def init_app():
    from database import init_db
    init_db()
    os.makedirs('output/videos', exist_ok=True)
    os.makedirs('temp', exist_ok=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/generate', methods=['POST'])
def generate():
    global current_pipeline
    data = request.get_json() or {}
    groq_key = data.get('groq_key', '').strip()

    if not groq_key:
        return jsonify({
            'error': (
                'Groq API key required. '
                'Get free key at console.groq.com'
            )
        }), 400

    if (current_pipeline and
            current_pipeline.progress.get('running')):
        return jsonify({
            'error': 'Already running. Please wait.'
        }), 400

    pexels_key = data.get('pexels_key', '').strip()
    pixabay_key = data.get('pixabay_key', '').strip()

    from database import save_keys
    save_keys(groq_key, pexels_key, pixabay_key)

    from pipeline_core import PhoenixPipeline
    current_pipeline = PhoenixPipeline(
        groq_key=groq_key,
        pexels_key=pexels_key,
        pixabay_key=pixabay_key,
        niche=data.get('niche', 'random mind-blowing facts'),
        tone=data.get('tone', 'shocking and dramatic'),
        audience=data.get('audience', 'everyone'),
        reference_urls=data.get('reference_urls', []),
        style_types=data.get('style_types', []),
        enable_evasion=data.get('enable_evasion', True)
    )

    count = max(1, min(50, int(data.get('count', 10))))

    from pipeline_runner import run as run_pipeline
    t = threading.Thread(
        target=run_pipeline,
        args=(current_pipeline, count),
        daemon=True
    )
    t.start()

    return jsonify({
        'status': 'started',
        'batch_id': current_pipeline.batch_id
    })


@app.route('/api/progress')
def progress():
    if not current_pipeline:
        return jsonify({
            'running': False,
            'phase': 0,
            'phase_name': '',
            'current_video': 0,
            'total_videos': 0,
            'percent': 0,
            'videos': [],
            'done': False,
            'error': '',
            'eta_seconds': 0,
            'successful': 0,
            'failed': 0
        })
    return jsonify(current_pipeline.progress)


@app.route('/api/download/video/<int:number>')
def dl_video(number):
    if not current_pipeline:
        return 'Not found', 404
    for v in current_pipeline.progress.get('videos', []):
        if v['number'] == number:
            p = v.get('video_path')
            if p and os.path.exists(p):
                return send_file(
                    p,
                    as_attachment=True,
                    download_name=f'phoenix_{number:03d}.mp4',
                    mimetype='video/mp4'
                )
    return 'Not found', 404


@app.route('/api/download/thumbnail/<int:number>')
def dl_thumb(number):
    if not current_pipeline:
        return 'Not found', 404
    for v in current_pipeline.progress.get('videos', []):
        if v['number'] == number:
            p = v.get('thumbnail_path')
            if p and os.path.exists(p):
                return send_file(
                    p,
                    as_attachment=True,
                    download_name=f'thumb_{number:03d}.png',
                    mimetype='image/png'
                )
    return 'Not found', 404


@app.route('/api/download/all')
def dl_all():
    if not current_pipeline:
        return 'Not found', 404
    buf = io.BytesIO()
    date = datetime.now().strftime('%Y%m%d')
    with zipfile.ZipFile(
        buf, 'w', zipfile.ZIP_DEFLATED
    ) as zf:
        for v in current_pipeline.progress.get('videos', []):
            if v['status'] == 'done':
                vp = v.get('video_path')
                tp = v.get('thumbnail_path')
                n = v['number']
                topic = v.get('topic', '')[:20]
                if vp and os.path.exists(vp):
                    zf.write(vp, f"video_{n:03d}_{topic}.mp4")
                if tp and os.path.exists(tp):
                    zf.write(tp, f"thumb_{n:03d}.png")
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name=f'phoenix_batch_{date}.zip',
        mimetype='application/zip'
    )


@app.route('/api/schedule')
def schedule():
    if not current_pipeline:
        return jsonify([])
    sp = getattr(current_pipeline, 'schedule_path', None)
    if sp and os.path.exists(sp):
        with open(sp) as f:
            return jsonify(json.load(f))
    return jsonify([])


@app.route('/api/save-keys', methods=['POST'])
def api_save():
    d = request.get_json() or {}
    from database import save_keys
    save_keys(
        d.get('groq_key', ''),
        d.get('pexels_key', ''),
        d.get('pixabay_key', '')
    )
    return jsonify({'status': 'saved'})


@app.route('/api/load-keys')
def api_load():
    from database import load_keys
    return jsonify(load_keys())


@app.route('/api/validate-keys')
def api_validate():
    from database import load_keys
    keys = load_keys()
    results = {
        'groq': 'unchecked',
        'pexels': 'unchecked',
        'pixabay': 'unchecked'
    }
    g = keys.get('groq_key', '')
    if g:
        try:
            r = req.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {g}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-70b-versatile",
                    "messages": [
                        {"role": "user", "content": "hi"}
                    ],
                    "max_tokens": 5
                },
                timeout=10
            )
            results['groq'] = (
                'valid' if r.status_code == 200 else 'invalid'
            )
        except Exception:
            results['groq'] = 'invalid'

    px = keys.get('pexels_key', '')
    if px:
        try:
            r = req.get(
                "https://api.pexels.com/v1/search",
                headers={"Authorization": px},
                params={"query": "nature", "per_page": 1},
                timeout=10
            )
            results['pexels'] = (
                'valid' if r.status_code == 200 else 'invalid'
            )
        except Exception:
            results['pexels'] = 'invalid'

    pb = keys.get('pixabay_key', '')
    if pb:
        try:
            r = req.get(
                "https://pixabay.com/api/",
                params={
                    "key": pb,
                    "q": "nature",
                    "per_page": 3
                },
                timeout=10
            )
            results['pixabay'] = (
                'valid' if r.status_code == 200 else 'invalid'
            )
        except Exception:
            results['pixabay'] = 'invalid'

    return jsonify(results)


if __name__ == '__main__':
    init_app()
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=False,
        use_reloader=False
    )
