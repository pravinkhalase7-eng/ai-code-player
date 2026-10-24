# play.doxstation.com

AI Code Player only publishes **UI :3010** and **API :8010**.

Public **:80 / :443** lives in the sibling repo **doxstation-proxy**. Proxy and TLS
changes belong there. This Jenkins job must not start nginx.

## DNS (one-time, Hostinger)

| Type | Name | Value |
|------|------|-------|
| A | `play` | `187.127.138.86` |

## App env

- `PUBLIC_APP_URL=https://play.doxstation.com`
- `NEXT_PUBLIC_API_URL=https://play.doxstation.com`
- `CORS_ORIGINS=https://play.doxstation.com,http://play.doxstation.com,http://localhost:3010`

Direct UI: `http://play.doxstation.com:3010/`
