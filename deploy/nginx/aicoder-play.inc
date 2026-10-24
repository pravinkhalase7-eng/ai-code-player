# Shared play.doxstation.com locations (HTTP + HTTPS).
# Variable proxy_pass + Docker DNS so nginx can start before backend/frontend
# are in DNS. A static "proxy_pass http://backend:8000" exits with
# "host not found in upstream" and never binds :80/:443.

resolver 127.0.0.11 valid=10s ipv6=off;
set $aicoder_api http://backend:8000;
set $aicoder_web http://frontend:3000;

location /.well-known/acme-challenge/ {
    root /var/www/html;
}

location /api/ {
    proxy_pass $aicoder_api$request_uri;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 120s;
}

location /audio/ {
    proxy_pass $aicoder_api$request_uri;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 120s;
}

location /images/ {
    proxy_pass $aicoder_api$request_uri;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 120s;
}

location / {
    proxy_pass $aicoder_web$request_uri;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 120s;
    proxy_send_timeout 120s;
    proxy_buffering off;
}
