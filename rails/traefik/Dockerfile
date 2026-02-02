FROM traefik:v2.10
COPY traefik.yaml /etc/traefik/traefik.yaml
COPY dynamic_conf.yaml /etc/traefik/dynamic_conf.yaml
# Ensure the certificates directory exists
RUN mkdir -p /letsencrypt && chmod 700 /letsencrypt
