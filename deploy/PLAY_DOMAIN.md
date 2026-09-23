# Map TECHSHALA to https://play.doxstation.com

Jenkins starts Compose service **nginx** on host **80 / 443** (same firewall path as `:3010`).

## 1. DNS (one-time, Hostinger)

| Type | Name | Value |
|------|------|-------|
| A | `play` | `187.127.138.86` |
| A | `@` (apex `doxstation.com`) | `187.127.138.86` |
| A | `shorts` | `187.127.138.86` |
| A | `docvault` | `187.127.138.86` |
| A | `manager` | `187.127.138.86` |

Wait until `dig +short play.doxstation.com @8.8.8.8` returns that IP.

## 2. Jenkins secret file

Use `ai-code-player.env.example` (upload as Secret file `ai-code-player-env-file`) with:

- `PUBLIC_APP_URL=https://play.doxstation.com`
- `NEXT_PUBLIC_API_URL=https://play.doxstation.com`
- `CORS_ORIGINS=https://play.doxstation.com,http://play.doxstation.com,http://localhost:3010`
- `NGINX_HTTP_PORT=80`
- `NGINX_HTTPS_PORT=443`

## 3. Jenkins deploy

Build with `PUBLIC_APP_URL=https://play.doxstation.com`. The Deploy stage starts `nginx`, which:

1. Binds host **80** and **443** through Docker
2. Proxies `play.doxstation.com` `/` → frontend and `/api` `/audio` `/images` → backend
3. Proxies `doxstation.com` `/` → host `:3000` (AI Teacher web) and `/api` → host `:8000` (AI Teacher API)
4. Proxies `shorts.doxstation.com` `/` → host `:3123` (Short Video Maker)
5. Proxies `docvault.doxstation.com` `/` → host `:8088` (DocVault)
6. Proxies `manager.doxstation.com` `/` → host `:3050` (Env Manager)
7. Serves Let's Encrypt HTTP-01 from `/var/www/html`
8. Host Nginx stage enables HTTPS when the cert exists

AI Teacher must keep publishing web on **3000** and API on **8000**. Do **not** start a second nginx on :80 for AI Teacher.

## 4. Smoke check

```bash
curl -fsS http://play.doxstation.com/ | head
curl -fsS https://play.doxstation.com/ | head
curl -fsS https://play.doxstation.com/api/v1/health
curl -fsS -H 'Host: doxstation.com' http://127.0.0.1/api/v1/health
curl -fsS http://doxstation.com/api/v1/health
curl -fsS -H 'Host: shorts.doxstation.com' http://127.0.0.1/health
curl -fsS https://shorts.doxstation.com/health
```

Direct UI (always): `http://play.doxstation.com:3010/`

## Notes

- Jenkins uses host **8080**, so nginx must not bind 8080.
- If certbot still times out, allow 80/443 on the Hostinger/cloud firewall, then rebuild.
- `aicoder-nginx` uses `host.docker.internal` (compose `extra_hosts: host-gateway`) to reach AI Teacher (`:3000`/`:8000`) and Short Video Maker (`:3123`).
- **Padlock / “connection is secure”** only appears on **https://**. `http://doxstation.com` will always show “Not secure”.
- Visiting `https://doxstation.com` before an apex cert exists fails: Docker serves the **play.doxstation.com** cert on :443, which does not match the apex name.

### Issue TLS for apex (padlock on doxstation.com)

```bash
# On VPS — HTTP-01 via existing aicoder nginx :80 ACME location
docker run --rm \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /var/lib/letsencrypt:/var/lib/letsencrypt \
  -v /var/www/html:/var/www/html \
  certbot/certbot certonly --webroot -w /var/www/html \
  -d doxstation.com -d www.doxstation.com \
  --non-interactive --agree-tos --register-unsafely-without-email

# Rebuild nginx so 40-https.sh loads the apex HTTPS vhost
cd /path/to/ai-coder   # or re-run AI Coder Jenkins
docker compose up -d --build --force-recreate --no-deps nginx

curl -fsS https://doxstation.com/api/v1/health
```

### Issue TLS for shorts (padlock on shorts.doxstation.com)

```bash
# DNS first: A record shorts → 187.127.138.86
docker run --rm \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /var/lib/letsencrypt:/var/lib/letsencrypt \
  -v /var/www/html:/var/www/html \
  certbot/certbot certonly --webroot -w /var/www/html \
  -d shorts.doxstation.com \
  --non-interactive --agree-tos --register-unsafely-without-email

# Rebuild nginx so 40-https.sh loads the shorts HTTPS vhost
cd /path/to/ai-coder   # or re-run AI Coder Jenkins
docker compose up -d --build --force-recreate --no-deps nginx

curl -fsS https://shorts.doxstation.com/health
```
