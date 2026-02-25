#!/bin/bash

echo "========================================"
echo "  E-Commerce Chatbot Launcher"
echo "========================================"
echo ""

echo "Checking Python installation..."
python3 --version
if [ $? -ne 0 ]; then
    echo "ERROR: Python is not installed"
    exit 1
fi

echo ""
echo "Starting Action Server..."
gnome-terminal -- bash -c "rasa run actions; exec bash" 2>/dev/null || \
xterm -e "rasa run actions" 2>/dev/null || \
osascript -e 'tell app "Terminal" to do script "cd \"'$(pwd)'\" && rasa run actions"' 2>/dev/null &

sleep 5

echo ""
echo "Starting Rasa Server..."
gnome-terminal -- bash -c "rasa run --enable-api --cors '*'; exec bash" 2>/dev/null || \
xterm -e "rasa run --enable-api --cors '*'" 2>/dev/null || \
osascript -e 'tell app "Terminal" to do script "cd \"'$(pwd)'\" && rasa run --enable-api --cors \"*\""' 2>/dev/null &

echo ""
echo "========================================"
echo "  Servers are starting..."
echo "========================================"
echo ""
echo "Action Server: http://localhost:5055"
echo "Rasa Server: http://localhost:5005"
echo ""
echo "Open rasa-webchat/index.html in your browser"
echo ""
