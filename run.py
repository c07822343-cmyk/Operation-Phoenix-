import sys
import os
import subprocess
import threading
import time
import webbrowser
import platform
import urllib.request
import urllib.error


def install_if_missing():
    packages = [
        ('flask', 'flask'),
        ('requests', 'requests'),
        ('edge_tts', 'edge-tts'),
        ('PIL', 'Pillow')
    ]
    for import_name, pkg_name in packages:
        try:
            __import__(import_name)
        except ImportError:
            print(f"Installing {pkg_name}...")
            subprocess.run(
                [sys.executable, '-m', 'pip',
                 'install', '-q', pkg_name],
                capture_output=True
            )


def check_ffmpeg():
    check_cmd = (
        ['which', 'ffmpeg']
        if platform.system() != 'Windows'
        else ['where', 'ffmpeg']
    )
    result = subprocess.run(
        check_cmd,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print("FFmpeg not found. Attempting install...")
        if platform.system() == 'Darwin':
            brew = subprocess.run(
                ['which', 'brew'],
                capture_output=True,
                text=True
            )
            if brew.returncode == 0:
                subprocess.run(
                    ['brew', 'install', 'ffmpeg'],
                    capture_output=True
                )
            else:
                print("Please run install.py first")
    else:
        print("FFmpeg ready")


def open_browser():
    print("Waiting for server to start...")
    for _ in range(40):
        time.sleep(1)
        try:
            urllib.request.urlopen(
                'http://127.0.0.1:5000',
                timeout=1
            )
            print("Opening browser...")
            webbrowser.open('http://127.0.0.1:5000')
            return
        except Exception:
            continue
    webbrowser.open('http://127.0.0.1:5000')


def create_folders():
    folders = ['output/videos', 'temp', 'assets']
    for f in folders:
        os.makedirs(f, exist_ok=True)


def main():
    print("")
    print("=" * 48)
    print("  PROJECT PHOENIX v3")
    print("  Faceless Shorts Factory")
    print("  Clearer Voice. Faster Production.")
    print("=" * 48)
    print("")

    create_folders()
    install_if_missing()
    check_ffmpeg()

    browser_thread = threading.Thread(
        target=open_browser,
        daemon=True
    )
    browser_thread.start()

    print("")
    print("Starting dashboard...")
    print("Your browser will open automatically.")
    print("Keep this window open while using Phoenix.")
    print("Close this window to stop.")
    print("")

    from main import app, init_app
    init_app()
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=False,
        use_reloader=False
    )


if __name__ == '__main__':
    main()
