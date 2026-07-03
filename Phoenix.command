#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

clear

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║        🔥 PROJECT PHOENIX                ║"
echo "║        Faceless Shorts Factory           ║"
echo "║                                          ║"
echo "║  Browser opens automatically.            ║"
echo "║  Keep this window open while using.      ║"
echo "║  Close this window to stop.              ║"
echo "╚══════════════════════════════════════════╝"
echo ""

if ! command -v python3 &>/dev/null; then
    echo "ERROR: Python 3 not found."
    echo "Download from: https://python.org"
    echo ""
    read -p "Press Enter to close..."
    exit 1
fi

if ! command -v ffmpeg &>/dev/null; then
    echo "FFmpeg not found. Running installer first..."
    python3 install.py
fi

echo "Starting Phoenix..."
echo ""

python3 run.py

echo ""
echo "Phoenix has stopped."
read -p "Press Enter to close this window..."
