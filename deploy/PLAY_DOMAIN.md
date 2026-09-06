# Map TECHSHALA to https://play.doxstation.com

Same pattern as **doc-vault**: Jenkins installs host nginx from git — no SSH required for routine deploys.

## 1. DNS (one-time, Hostinger)

| Type | Name | Value |
|------|------|-------|
| A | `play` | `187.127.138.86` |

Wait until `dig +short play.doxstation.com @8.8.8.8` returns that IP.

## 2. Jenkins deploy

Build with:

- `PUBLIC_APP_URL` = `https://play.doxstation.com` (default)
- Secret `ai-code-player-env-file`

Post-Deploy runs `scripts/install_host_nginx.sh`, which:

1. Writes `/etc/nginx/sites-available/aicoder` (HTTP bootstrap → `:3010`)
2. Requests Let's Encrypt if the cert is missing (certbot webroot via Docker)
3. Switches to HTTPS when the cert exists
4. Reloads host nginx (HUP) — no SSH

## 3. Smoke check

```bash
curl -fsS https://play.doxstation.com/ | head
curl -fsS https://play.doxstation.com/api/v1/health
```

## Notes

- UI stays on host port `3010`; API on `8010`. Public traffic uses the domain only.
- If certbot fails (DNS not ready), the site still works on **http://play.doxstation.com** until the next successful deploy.
- Compose profile `proxy` on `:8080` is optional and separate.
