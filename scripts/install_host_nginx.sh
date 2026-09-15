#!/usr/bin/env bash
# Publish play.doxstation.com on Docker :80/:443 (same firewall path as :3010).
# Host nginx is optional and often not running on this VPS.
set -euo pipefail

DOMAIN="${PUBLIC_HOST:-}"
if [ -z "$DOMAIN" ]; then
  DOMAIN="${PUBLIC_APP_URL:-play.doxstation.com}"
fi
DOMAIN="${DOMAIN#https://}"
DOMAIN="${DOMAIN#http://}"
DOMAIN="${DOMAIN%%/*}"
DOMAIN="${DOMAIN%%:*}"

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/docker-compose.yml"
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-aicoder}"
export NGINX_SERVER_NAME="${DOMAIN}"

HOST_HTTP_TEMPLATE="${ROOT_DIR}/deploy/host-nginx-aicoder.http.conf"
HOST_HTTPS_TEMPLATE="${ROOT_DIR}/deploy/host-nginx-aicoder.conf"

if [ ! -f "${ROOT_DIR}/deploy/nginx/Dockerfile" ] || [ ! -f "${ROOT_DIR}/deploy/nginx/default.conf" ]; then
  echo "Missing baked nginx image files under deploy/nginx/"
  exit 1
fi

if [ -z "$DOMAIN" ]; then
  echo "PUBLIC_HOST / PUBLIC_APP_URL empty — skip nginx"
  exit 0
fi

cert_exists() {
  docker run --rm \
    -v /etc/letsencrypt:/etc/letsencrypt:ro \
    alpine:3.20 \
    sh -c "test -f /etc/letsencrypt/live/${DOMAIN}/fullchain.pem && test -f /etc/letsencrypt/live/${DOMAIN}/privkey.pem"
}

nginx_answers() {
  docker compose -f "$COMPOSE_FILE" exec -T nginx wget -qO- http://127.0.0.1/ >/dev/null 2>&1 \
    || docker compose -f "$COMPOSE_FILE" exec -T frontend wget -qO- http://nginx/ >/dev/null 2>&1
}

reload_nginx() {
  docker compose -f "$COMPOSE_FILE" exec -T nginx nginx -s reload
}

start_nginx() {
  echo "Starting Docker nginx on host :80/:443 → play.doxstation.com (${DOMAIN})"
  docker compose -f "$COMPOSE_FILE" up -d --build --force-recreate --no-deps nginx
  i=1
  while [ "$i" -le 20 ]; do
    if nginx_answers; then
      echo "nginx is serving HTTP on :80"
      return 0
    fi
    echo "attempt ${i}: nginx starting"
    i=$((i + 1))
    sleep 1
  done
  echo "ERROR: nginx did not answer on :80"
  docker compose -f "$COMPOSE_FILE" logs --tail=80 nginx || true
  echo "If bind failed, something else owns port 80. :3010 still works."
  return 1
}

prepare_webroot() {
  docker run --rm \
    -v /var/www/html:/var/www/html \
    alpine:3.20 \
    sh -c 'mkdir -p /var/www/html/.well-known/acme-challenge && chmod -R a+rX /var/www/html'
}

issue_cert_if_needed() {
  if cert_exists; then
    echo "TLS cert already present for ${DOMAIN}"
    return 0
  fi

  echo "No TLS cert for ${DOMAIN} — requesting Let's Encrypt via certbot (webroot)"
  prepare_webroot
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
    echo "WARN: certbot failed. http://${DOMAIN} should still work via Docker :80."
    return 1
  fi
  return 0
}

# Host nginx copy is best-effort (doc-vault). Compose `nginx` is what serves :80.
try_host_nginx_copy() {
  if [ ! -f "$HOST_HTTP_TEMPLATE" ] || [ ! -f "$HOST_HTTPS_TEMPLATE" ]; then
    return 0
  fi
  local rendered
  rendered="$(mktemp)"
  sed "s/__DOMAIN__/${DOMAIN}/g" "$HOST_HTTP_TEMPLATE" > "$rendered"
  docker run --rm -i \
    -v /etc/nginx/sites-available:/sites-available \
    -v /etc/nginx/sites-enabled:/sites-enabled \
    alpine:3.20 \
    sh -c "cat > /sites-available/aicoder && ln -sfn /sites-available/aicoder /sites-enabled/aicoder" \
    < "$rendered" >/dev/null 2>&1 || true
  rm -f "$rendered"
}

start_nginx
try_host_nginx_copy || true

if issue_cert_if_needed && cert_exists; then
  docker compose -f "$COMPOSE_FILE" up -d --force-recreate --no-deps nginx
  i=1
  while [ "$i" -le 10 ]; do
    if nginx_answers; then
      break
    fi
    i=$((i + 1))
    sleep 1
  done
  reload_nginx || true
  echo "nginx ready: https://${DOMAIN} and http://${DOMAIN} → frontend:3000"
else
  echo "nginx ready: http://${DOMAIN} → frontend:3000 (same app as :3010)"
  echo "https://${DOMAIN} needs a Let's Encrypt cert; re-run after :80 is reachable from the internet."
fi
