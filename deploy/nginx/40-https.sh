#!/bin/sh
# Enable TLS only when Let's Encrypt files are already on the host volume.
set -eu

DOMAIN="${NGINX_SERVER_NAME:-play.doxstation.com}"
DOMAIN="${DOMAIN#https://}"
DOMAIN="${DOMAIN#http://}"
DOMAIN="${DOMAIN%%/*}"
DOMAIN="${DOMAIN%%:*}"

CERT="/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
KEY="/etc/letsencrypt/live/${DOMAIN}/privkey.pem"
TPL="/etc/nginx/templates-extra/https.conf.template"
OUT="/etc/nginx/conf.d/10-https.conf"

if [ -n "$DOMAIN" ] && [ -f "$CERT" ] && [ -f "$KEY" ] && [ -f "$TPL" ]; then
  sed "s/__DOMAIN__/${DOMAIN}/g" "$TPL" > "$OUT"
  echo "nginx: HTTPS enabled for ${DOMAIN}"
else
  rm -f "$OUT"
  echo "nginx: HTTP only (no cert yet for ${DOMAIN:-unknown})"
fi
