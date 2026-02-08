FROM ghcr.io/linuxserver/webtop:ubuntu-xfce

# Install dependencies and Rocrail
# We use the PiOS11-ARM64 build which is compatible with Ubuntu 20+ ARM64
RUN \
  apt-get update && \
  DEBIAN_FRONTEND=noninteractive apt-get install -y \
    curl \
    wget \
    unzip \
    socat \
    libwxgtk3.2-1t64 \
    libusb-1.0-0 \
    libcanberra-gtk3-module && \
  mkdir -p /opt/rocrail && \
  curl -L -o /tmp/rocrail.zip https://wiki.rocrail.net/rocrail-snapshot/Rocrail-PiOS11-ARM64.zip && \
  unzip /tmp/rocrail.zip -d /opt/rocrail && \
  rm /tmp/rocrail.zip && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

# Add rocraild as a proper S6 service (minimal launcher)
RUN mkdir -p /etc/services.d/rocraild
COPY rocraild-run.sh /etc/services.d/rocraild/run
RUN chmod +x /etc/services.d/rocraild/run

# Force rebuild by bumping version
LABEL app_version="vanilla-v2"

# Expose ports: 
# 3000: WebTop (Rocview GUI)
# 8088: Rocweb (Browser control)
# 8051: Rocrail Server
EXPOSE 3000 8088 8051

# Symlink rocrail for ease of use
RUN ln -s /opt/rocrail/bin/rocrail /usr/local/bin/rocrail && \
    ln -s /opt/rocrail/bin/rocview /usr/local/bin/rocview
