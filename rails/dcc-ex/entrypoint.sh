#!/bin/sh
# This script ensures the latest bridge.py is available in the shared volume.
# If we are in 'development' mode (volume persists), we might want to preserve edits.
# However, for now, we'll ensure that a fresh deploy updates the code.

if [ -f /app_backup/bridge.py ]; then
    # Check if they are different
    if ! cmp -s /app_backup/bridge.py /app/bridge.py; then
        echo "Updating bridge.py in shared volume from deployment backup..."
        cp /app_backup/bridge.py /app/bridge.py
    fi
fi

if [ ! -f /app/entrypoint.sh ]; then
    cp /usr/local/bin/entrypoint.sh /app/entrypoint.sh
fi

echo "Starting DCC-EX Bridge..."
exec python bridge.py
