#!/bin/bash
# Be More Agent - Start Script for Raspberry Pi with DSI display
# Usage: ./start.sh

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$BASE_DIR" || exit 1

# Activate virtual environment
source venv/bin/activate 2>/dev/null || { echo "ERROR: venv not found"; exit 1; }

# Check if ollama is running
if ! pgrep -x ollama > /dev/null; then
    echo "Starting Ollama..."
    sudo systemctl start ollama
    sleep 2
fi

echo "Starting Be More Agent on DSI display..."
echo "Press ESC to exit fullscreen"
echo "Press ENTER for push-to-talk (when mic is connected)"
echo ""

# There's already a Wayland+Xwayland desktop running on :0
# Just launch the agent with DISPLAY set
export DISPLAY=:0
exec ./venv/bin/python agent.py 2>&1
