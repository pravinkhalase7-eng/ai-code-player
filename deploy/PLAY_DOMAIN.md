# Map TECHSHALA to https://play.doxstation.com

Jenkins publishes the tutor on **Docker :80 / :443** (same firewall path as `:3010`). Host nginx is optional.

## 1. DNS (one-time, Hostinger)

| Type | Name | Value |
|------|------|-------|
| A | `play` | `187.127.138.86` |

Wait until `dig +short play.doxstation.com @8.8.8.8` returns that IP.

## 2. Jenkins deploy

Build with:

- `PUBLIC_APP_URL` = `https://play.doxstation.com` (default)
- Secret `ai-code-player-env-file`

The **Host Nginx** stage starts Compose service `edge`:

1. Binds host **80** and **443** through Docker (bypasses ufw the same way `:3010` does)
2. Proxies `/` to the frontend container (`:3010` still works directly)
3. Serves Let's Encrypt HTTP-01 from `/var/www/html`
4. Enables HTTPS when the cert exists

## 3. Smoke check

```bash
curl -fsS http://play.doxstation.com/ | head
curl -fsS https://play.doxstation.com/ | head
curl -fsS https://play.doxstation.com/api/v1/health
```

Direct UI (always): `http://play.doxstation.com:3010/`

## Notes

- Jenkins uses host **8080**, so edge must not bind 8080.
- If certbot still times out, a cloud/Hostinger panel firewall is dropping 80/443 — allow those ports, then rebuild.
