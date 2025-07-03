# Use Python 3.12 slim image
FROM python:3.12-slim

# Install Linux packages required for Playwright browsers
RUN apt-get update && \
    apt-get install -y \
        wget \
        curl \
        gnupg \
        fonts-liberation \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libcups2 \
        libdbus-1-3 \
        libdrm2 \
        libgbm1 \
        libgtk-3-0 \
        libnspr4 \
        libnss3 \
        libx11-xcb1 \
        libxcomposite1 \
        libxdamage1 \
        libxrandr2 \
        xdg-utils \
        libasound2 \
        libxss1 \
        libxtst6 \
        libxshmfence1 \
        libsecret-1-0 \
        libenchant-2-2 \
        libmanette-0.2-0 \
        libgles2 \
        libsoup-3.0-0 \
        libgstgl1.0-0 \
        libgstreamer-plugins-bad1.0-0 \
        libgstcodecparsers-1.0-0 && \
    rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy all files into container
COPY . .

# Install Python requirements
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Install Playwright browsers and dependencies
RUN playwright install --with-deps

# Run your start.sh
CMD ["./start.sh"]