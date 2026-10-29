#!/bin/sh
# Runs on container start (nginx image: /docker-entrypoint.d). Creates a self-signed certificate unless a real one is mounted.
set -e
CERT_DIR=/etc/nginx/certs
if [ ! -f "$CERT_DIR/cert.pem" ] || [ ! -f "$CERT_DIR/key.pem" ]; then
  mkdir -p "$CERT_DIR"
  openssl req -x509 -newkey rsa:2048 -nodes -days 365 -subj "/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,DNS:web,IP:127.0.0.1" \
    -keyout "$CERT_DIR/key.pem" -out "$CERT_DIR/cert.pem" 2>/dev/null
  echo "40-selfsigned-cert.sh: generated a self-signed development certificate (replace it in production)"
fi
