# Map TECHSHALA to https://play.doxstation.com

Staging app today: `http://187.127.138.86:3010` (API `:8010`).

## 1. DNS (Hostinger / dns-parking for doxstation.com)

Create:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | `play` | `187.127.138.86` | 300 |

Wait until `dig +short play.doxstation.com @8.8.8.8` returns `187.127.138.86`.

## 2. Jenkins deploy with the public URL

Build with:

- `PUBLIC_APP_URL` = `https://play.doxstation.com`
- `DEPLOY_ENV` = `staging` or `production`
- Secret credential `ai-code-player-env-file` (unchanged)

That sets `CORS_ORIGINS` and `NEXT_PUBLIC_API_URL` to the domain so the browser talks same-origin through Next rewrites.

## 3. TLS reverse proxy on the server (SSH)

```bash
sudo apt-get update
sudo apt-get install -y nginx certbot python3-certbot-nginx

# from the ai-code-player checkout on the box:
sudo cp deploy/play.doxstation.com.conf /etc/nginx/sites-available/play.doxstation.com
sudo ln -sf /etc/nginx/sites-available/play.doxstation.com /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# after DNS propagates:
sudo certbot --nginx -d play.doxstation.com
```

Certbot will add HTTPS listen 443 and redirect HTTP→HTTPS.

## 4. Smoke check

```bash
curl -fsS https://play.doxstation.com/ | head
curl -fsS https://play.doxstation.com/api/v1/health
```

Open https://play.doxstation.com in a browser.

## Notes

- Direct ports `:3010` / `:8010` can stay open for debugging; public users should use the domain only.
- Compose profile `proxy` (`deploy/nginx.conf` on `:8080`) is optional and separate from this host nginx site.
