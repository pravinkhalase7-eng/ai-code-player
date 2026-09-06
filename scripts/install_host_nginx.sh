#!/usr/bin/env bash
# Copy deploy/host-nginx-aicoder*.conf onto the VPS host nginx.
# Safe to run from Jenkins (host Docker socket) — same approach as doc-vault.
set -euo pipefail

DOMAIN="${PUBLIC_HOST:-}"
if [ -z "$DOMAIN" ]; then
  DOMAIN="${PUBLIC_APP_URL:-play.doxstation.com}"
fi
DOMAIN="${DOMAIN#https://}"
DOMAIN="${DOMAIN#http://}"
DOMAIN="${DOMAIN%%/*}"
DOMAIN="${DOMAIN%%:*}"

SITE_NAME="aicoder"
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HTTPS_TEMPLATE="${ROOT_DIR}/deploy/host-nginx-aicoder.conf"
HTTP_TEMPLATE="${ROOT_DIR}/deploy/host-nginx-aicoder.http.conf"
CERT_LIVE="/etc/letsencrypt/live/${DOMAIN}"

if [ ! -f "$HTTPS_TEMPLATE" ] || [ ! -f "$HTTP_TEMPLATE" ]; then
  echo "Missing host nginx templates under deploy/"
  exit 1
fi

if [ -z "$DOMAIN" ]; then
  echo "PUBLIC_HOST / PUBLIC_APP_URL empty — skip host nginx"
  exit 0
fi

render() {
  local template="$1"
  local dest="$2"
  sed "s/__DOMAIN__/${DOMAIN}/g" "$template" > "$dest"
}

install_site() {
  local rendered="$1"
  echo "Installing host nginx site ${SITE_NAME} for ${DOMAIN}"
  docker run --rm -i \
    -v /etc/nginx/sites-available:/sites-available \
    -v /etc/nginx/sites-enabled:/sites-enabled \
    alpine:3.20 \
    sh -c "cat > /sites-available/${SITE_NAME} && ln -sfn /sites-available/${SITE_NAME} /sites-enabled/${SITE_NAME}" \
    < "$rendered"
}

reload_nginx() {
  docker run --rm --pid=host \
    -v /run:/host-run:ro \
    alpine:3.20 \
    sh -c 'if [ -f /host-run/nginx.pid ]; then kill -HUP "$(cat /host-run/nginx.pid)"; echo "nginx HUP ok"; else echo "Copied site file; reload nginx on the host if needed"; fi'
}

cert_exists() {
  docker run --rm \
    -v /etc/letsencrypt:/etc/letsencrypt:ro \
    alpine:3.20 \
    sh -c "test -f /etc/letsencrypt/live/${DOMAIN}/fullchain.pem && test -f /etc/letsencrypt/live/${DOMAIN}/privkey.pem"
}

issue_cert_if_needed() {
  if cert_exists; then
    echo "TLS cert already present for ${DOMAIN}"
    return 0
  fi

  echo "No TLS cert for ${DOMAIN} — requesting Let's Encrypt via certbot (webroot)"
  docker run --rm \
    -v /var/www/html:/var/www/html \
    alpine:3.20 \
    sh -c 'mkdir -p /var/www/html/.well-known/acme-challenge && chmod -R a+rX /var/www/html'

  # Ensure HTTP site is live before ACME challenge.
  rendered_http="$(mktemp)"
  render "$HTTP_TEMPLATE" "$rendered_http"
  install_site "$rendered_http"
  reload_nginx
  rm -f "$rendered_http"
  sleep 2

  set +e
  docker run --rm \
    -v /etc/letsencrypt:/etc/letsencrypt \
    -v /var/lib/letsencrypt:/var/lib/letsencrypt \
    -v /var/www/html:/var/www/html \
    certbot/certbot \
    certonly --webroot -w /var/www/html \
      -d "$DOMAIN" \
      --non-interactive --agree-tos --register-unsafely-without-email \
      --keep-until-expiring
  status=$?
  set -e
  if [ "$status" -ne 0 ]; then
    echo "WARN: certbot failed (DNS may not point here yet). Leaving HTTP proxy for ${DOMAIN}."
    return 1
  fi
  return 0
}

rendered="$(mktemp)"
trap 'rm -f "$rendered"' EXIT

# Always publish HTTP first so the hostname answers even before certs.
render "$HTTP_TEMPLATE" "$rendered"
install_site "$rendered"
reload_nginx

if issue_cert_if_needed && cert_exists; then
  render "$HTTPS_TEMPLATE" "$rendered"
  install_site "$rendered"
  reload_nginx
  echo "Host nginx ready: https://${DOMAIN} → 127.0.0.1:3010"
else
  echo "Host nginx ready (HTTP): http://${DOMAIN} → 127.0.0.1:3010"
  echo "After DNS A record ${DOMAIN} → this VPS, re-run Jenkins deploy to obtain TLS."
fi
