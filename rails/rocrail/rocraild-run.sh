#!/usr/bin/with-contenv bash
set -e

echo "[rocraild-service] Starting plain Rocrail server..."

# Ensure directory exists and permissions are correct for the abc user
mkdir -p /config/Rocrail
chown -R abc:abc /config/Rocrail
chmod -R 775 /config/Rocrail

echo "[rocraild-service] Executing: /opt/rocrail/bin/rocrail -w /config/Rocrail -i rocrail.ini -l /opt/rocrail/bin"
exec s6-setuidgid abc /opt/rocrail/bin/rocrail -w /config/Rocrail -i rocrail.ini -l /opt/rocrail/bin
