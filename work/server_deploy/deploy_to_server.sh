#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/quiet-atlas-api}"
SITE_DIR="${SITE_DIR:-/opt/quiet-atlas-site}"
API_PORT="${API_PORT:-8787}"
SITE_PORT="${SITE_PORT:-4173}"

sudo mkdir -p "$APP_DIR" "$SITE_DIR"
sudo cp train_ticket_assisted_server.py "$APP_DIR/"
sudo cp requirements.txt "$APP_DIR/"
sudo cp train-ticket.env.example "$APP_DIR/train-ticket.env"

if [ ! -d "$APP_DIR/venv" ]; then
  sudo python3 -m venv "$APP_DIR/venv"
fi

sudo "$APP_DIR/venv/bin/pip" install --upgrade pip
sudo "$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"
sudo "$APP_DIR/venv/bin/playwright" install chromium

sudo cp quiet-atlas-train.service /etc/systemd/system/quiet-atlas-train.service
sudo sed -i "s/--port 8787/--port ${API_PORT}/" /etc/systemd/system/quiet-atlas-train.service
sudo systemctl daemon-reload
sudo systemctl enable --now quiet-atlas-train.service

cat <<EOF
API service installed.
Health check:
  curl http://127.0.0.1:${API_PORT}/health

Static site directory:
  ${SITE_DIR}
EOF
