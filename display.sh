#!/usr/bin/env bash
# Virtual display for solving CAPTCHAs on a headless machine (e.g. Termux +
# proot on Android, which has no screen of its own).
#
# Starts, in a detached tmux session named "display":
#   Xvnc :1   - TigerVNC: an invisible X screen that main.py opens its CAPTCHA
#               window on, served over VNC on 127.0.0.1:5901 only, no password
#   openbox   - minimal window manager (lets the window maximize/move)
# View it with any VNC app on the same phone (e.g. AVNC -> 127.0.0.1:5901,
# gesture style "Touchscreen" so dragging puzzle pieces works).
#
# Xvfb + x11vnc was tried first: under proot, x11vnc accepted TCP connections
# but never answered the VNC handshake, so viewers hung at "connecting".
#
# Usage: ./display.sh start|stop|status
# Resolution: RES=1600x900 ./display.sh start   (default 1280x720)
set -u

NUM=1
PORT=5901
SESSION=display
RES=${RES:-1280x720}
SOCK=/tmp/.X11-unix/X$NUM

running() { tmux has-session -t "$SESSION" 2>/dev/null; }

kill_procs() {
    # Killing the tmux session doesn't reliably take its programs down under
    # proot, so end them by exact process name too.
    pkill -x Xvnc 2>/dev/null
    pkill -x openbox 2>/dev/null
    sleep 0.5
    rm -f "/tmp/.X$NUM-lock" "$SOCK"
}

start() {
    if running && [ -S "$SOCK" ]; then
        echo "Display :$NUM is already running (VNC: 127.0.0.1:$PORT)."
        return 0
    fi
    tmux kill-session -t "$SESSION" 2>/dev/null
    kill_procs
    tmux new-session -d -s "$SESSION" -n vnc \
        "Xvnc :$NUM -geometry $RES -depth 24 -localhost=1 -SecurityTypes None -rfbport $PORT -nolisten tcp"
    for _ in $(seq 50); do
        [ -S "$SOCK" ] && break
        sleep 0.1
    done
    if [ ! -S "$SOCK" ]; then
        echo "Xvnc failed to start (see: tmux attach -t $SESSION)." >&2
        return 1
    fi
    tmux new-window -d -t "$SESSION" -n wm "DISPLAY=:$NUM openbox"
    echo "Display :$NUM started ($RES). VNC: 127.0.0.1:$PORT"
}

stop() {
    tmux kill-session -t "$SESSION" 2>/dev/null
    kill_procs
    echo "Display stopped."
}

status() {
    if running && [ -S "$SOCK" ]; then
        echo "Running: display :$NUM, VNC on 127.0.0.1:$PORT"
        tmux list-windows -t "$SESSION" -F '  #{window_name}: #{pane_current_command}'
    else
        echo "Not running. Start it with: ./display.sh start"
        return 1
    fi
}

case "${1:-}" in
    start) start ;;
    stop) stop ;;
    status) status ;;
    *) echo "Usage: $0 start|stop|status" >&2; exit 2 ;;
esac
