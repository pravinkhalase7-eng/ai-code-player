# Bake vhost config into the image. Jenkins-in-Docker + host docker.sock cannot
# bind-mount ./deploy/edge.d from the Jenkins workspace path.
FROM nginx:1.27-alpine
COPY default.conf /etc/nginx/conf.d/default.conf
COPY https.conf.template /etc/nginx/templates-extra/https.conf.template
COPY https-default.conf.template /etc/nginx/templates-extra/https-default.conf.template
COPY https-aiteacher.conf.template /etc/nginx/templates-extra/https-aiteacher.conf.template
COPY https-shortvideo.conf.template /etc/nginx/templates-extra/https-shortvideo.conf.template
COPY https-docvault.conf.template /etc/nginx/templates-extra/https-docvault.conf.template
COPY 40-https.sh /docker-entrypoint.d/40-https.sh
RUN chmod +x /docker-entrypoint.d/40-https.sh
