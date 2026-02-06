#!/bin/bash

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

DOMAIN=${RAILS_DOMAIN:-rails49.org}
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Starting Rails49 Service Infrastructure Tests ===${NC}"
echo "Target Domain: $DOMAIN"
echo ""

errors=0

check_status() {
    if [ $1 -eq 0 ]; then
        echo -e "[ ${GREEN}OK${NC} ] $2"
    else
        echo -e "[ ${RED}FAIL${NC} ] $2"
        errors=$((errors + 1))
    fi
}

echo -e "${BLUE}--- Testing HTTP/HTTPS Services ---${NC}"

# 1. HTTP to HTTPS Redirect
curl -s -I "http://ui.$DOMAIN" | grep -qi "Location: https://"
check_status $? "HTTP to HTTPS Redirection (ui.$DOMAIN)"

# 2. UI Accessibility
curl -s -fL "https://ui.$DOMAIN" | grep -qi "MQTT"
check_status $? "UI Page Accessibility (https://ui.$DOMAIN)"

# 3. Base Domain Accessibility (Ignored - used otherwise)
# curl -s -fL "https://$DOMAIN" | grep -qi "MQTT"
# check_status $? "Base Domain Accessibility (https://$DOMAIN)"

# 4. VS Code Accessibility 
curl -s -o /dev/null -w "%{http_code}" "https://code.$DOMAIN" | grep -E "200|301|302|401" > /dev/null
check_status $? "VS Code Accessibility (https://code.$DOMAIN)"

# 5. Traefik Dashboard Accessibility
curl -s -o /dev/null -w "%{http_code}" -k "https://traefik.$DOMAIN/dashboard/" | grep -q "200"
check_status $? "Traefik Dashboard Accessibility (https://traefik.$DOMAIN)"

echo ""
echo -e "${BLUE}--- Testing SSL Certificates ---${NC}"

# 5. Wildcard Certificate Check
cert_info=$(echo | openssl s_client -connect "ui.$DOMAIN:443" -servername "ui.$DOMAIN" 2>/dev/null | openssl x509 -noout -text)
echo "$cert_info" | grep -qi "DNS:*.$DOMAIN"
check_status $? "Wildcard SAN in Certificate (*.$DOMAIN)"

echo ""
echo -e "${BLUE}--- Testing MQTT Services ---${NC}"

# 6. Raw MQTT (1883)
nc -zv -w 5 "mqtt.$DOMAIN" 1883 2>&1 | grep -q "succeeded"
check_status $? "Raw MQTT Port 1883 Connectivity"

# 7. Python MQTT Client Connectivity (via uv)
uv run python3 tests/test_mqtt.py
check_status $? "Python MQTT Client Connectivity (TCP & TLS)"

# 8. MQTTS Port 8883 Handshake
# Using openssl to verify TLS handshake on 8883
echo | openssl s_client -connect "mqtt.$DOMAIN:8883" -servername "mqtt.$DOMAIN" 2>/dev/null | grep -q "CONNECTED"
check_status $? "MQTTS Port 8883 TLS Handshake"

# 9. MQTT WebSockets (443)
uv run python3 tests/test_ws.py
check_status $? "MQTT WebSocket Handshake (wss://mqtt.$DOMAIN)"

# 10. DCC-EX Service Functional Test (TCP & MQTT)
uv run python3 tests/test_dcc.py
check_status $? "DCC-EX Service (TCP 2560 & MQTT Integration)"

echo ""
if [ $errors -eq 0 ]; then
    echo -e "${GREEN}=== ALL TESTS PASSED ===${NC}"
    exit 0
else
    echo -e "${RED}=== $errors TESTS FAILED ===${NC}"
    exit 1
fi
