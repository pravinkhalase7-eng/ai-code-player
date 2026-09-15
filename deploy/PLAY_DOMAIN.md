# Map TECHSHALA to https://play.doxstation.com

Jenkins starts Compose service **nginx** on host **80 / 443** (same firewall path as `:3010`).

## 1. DNS (one-time, Hostinger)

| Type | Name | Value |
|------|------|-------|
| A | `play` | `187.127.138.86` |

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
2. Proxies `/` to the frontend and `/api` `/audio` `/images` to the backend
3. Serves Let's Encrypt HTTP-01 from `/var/www/html`
4. Host Nginx stage enables HTTPS when the cert exists

## 4. Smoke check

```bash
curl -fsS http://play.doxstation.com/ | head
curl -fsS https://play.doxstation.com/ | head
curl -fsS https://play.doxstation.com/api/v1/health
```

Direct UI (always): `http://play.doxstation.com:3010/`

## Notes

- Jenkins uses host **8080**, so nginx must not bind 8080.
- If certbot still times out, allow 80/443 on the Hostinger/cloud firewall, then rebuild.
