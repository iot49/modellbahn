FROM lscr.io/linuxserver/baseimage-ubuntu:noble

# Install dependencies and Rocrail
# PiOS11-ARM64 build is compatible with Ubuntu 24.04 ARM64
RUN \
  apt-get update && \
  DEBIAN_FRONTEND=noninteractive apt-get install -y \
    curl \
    wget \
    unzip \
    libwxgtk3.2-1t64 \
    libusb-1.0-0 && \
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

# Force rebuild
LABEL app_version="headless-v1"

# Expose port 8051 for native client connection
EXPOSE 8051

# Symlink rocrail for ease of use
RUN ln -s /opt/rocrail/bin/rocrail /usr/local/bin/rocrail
