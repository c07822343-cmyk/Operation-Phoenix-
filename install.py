import subprocess
import sys
import os
import platform


def clear():
    os.system('clear' if os.name != 'nt' else 'cls')


def main():
    clear()
    print("")
    print("=" * 52)
    print("   PROJECT PHOENIX — ONE TIME SETUP")
    print("   After this just double click")
    print("   Phoenix.command to start.")
    print("=" * 52)
    print("")

    print("Step 1: Installing Python packages...")
    packages = ['flask', 'requests', 'edge-tts', 'Pillow']
    for pkg in packages:
        print(f"  {pkg}...", end='', flush=True)
        result = subprocess.run(
            [sys.executable, '-m', 'pip',
             'install', '-q', '--upgrade', pkg],
            capture_output=True
        )
        print(" done" if result.returncode == 0 else " FAILED")
    print("")

    print("Step 2: Installing FFmpeg...")
    if platform.system() == 'Darwin':
        check = subprocess.run(
            ['which', 'ffmpeg'],
            capture_output=True,
            text=True
        )
        if check.returncode == 0:
            print("  FFmpeg already installed.")
        else:
            brew = subprocess.run(
                ['which', 'brew'],
                capture_output=True,
                text=True
            )
            if brew.returncode != 0:
                print("  Installing Homebrew...")
                print("  This may ask for your Mac password.")
                cmd = (
                    '/bin/bash -c "$(curl -fsSL '
                    'https://raw.githubusercontent.com/'
                    'Homebrew/install/HEAD/install.sh)"'
                )
                subprocess.run(cmd, shell=True)
            print("  Installing FFmpeg via Homebrew...")
            subprocess.run(
                ['brew', 'install', 'ffmpeg']
            )
    else:
        print("  Please install FFmpeg from ffmpeg.org")
    print("")

    print("Step 3: Creating folders...")
    folders = [
        'output/videos', 'temp', 'assets',
        'templates', 'static'
    ]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
    print("  Done")
    print("")

    print("Step 4: Setting up launcher...")
    if os.path.exists('Phoenix.command'):
        subprocess.run(['chmod', '+x', 'Phoenix.command'])
        print("  Phoenix.command ready to double click")
    print("")

    print("Step 5: Verifying...")
    ffmpeg = subprocess.run(
        ['ffmpeg', '-version'], capture_output=True
    )
    print(
        f"  FFmpeg: "
        f"{'OK' if ffmpeg.returncode == 0 else 'MISSING - install from ffmpeg.org'}"
    )
    checks = [
        ('flask', 'Flask'),
        ('requests', 'requests'),
        ('edge_tts', 'edge-tts'),
        ('PIL', 'Pillow')
    ]
    for imp, name in checks:
        try:
            __import__(imp)
            print(f"  {name}: OK")
        except ImportError:
            print(f"  {name}: MISSING")
    print("")

    print("=" * 52)
    print("  SETUP COMPLETE")
    print("")
    print("  TO START PHOENIX:")
    print("  Double click: Phoenix.command")
    print("")
    print("  FIRST TIME ONLY:")
    print("  Right click Phoenix.command")
    print("  Get Info > Open With > Terminal")
    print("=" * 52)
    print("")
    input("Press Enter to close...")


main()
