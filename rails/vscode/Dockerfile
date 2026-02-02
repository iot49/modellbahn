FROM linuxserver/code-server:latest

# Enable passwordless sudo for the abc user
# The linuxserver images use 'abc' as the default user (UID 1000)
RUN echo "abc ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/abc && \
    chmod 0440 /etc/sudoers.d/abc

# Copy the contents of the rails directory into the workspace
COPY . /workspace
