FROM python:3.12-slim

# Install OS dependencies required for Playwright
RUN apt-get update && \
    apt-get install -y \
        wget curl gnupg \
        fonts-liberation libatk-bridge2.0-0 libatk1.0-0 libcups2 libdbus-1-3 libdrm2 libgbm1 \
        libgtk-3-0 libnspr4 libnss3 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 \
        xdg-utils libasound2 libxss1 libxtst6 libxshmfence1 libsecret-1-0 libenchant-2-2 \
        libmanette-0.2-0 libgles2-mesa libsoup-3.0-0 libgstreamer-gl1.0-0 \
        libgstreamer-plugins-bad1.0-0 libgstcodecparsers-1.0-0 libgl1-mesa-glx \
        libgl1-mesa-dri libegl1-mesa libwayland-egl1-mesa libxkbcommon0 \
        git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the rest of your code
COPY . .

# Install Chromium for Python Playwright
RUN python -m playwright install chromium

# Ensure start.sh is executable
RUN chmod +x /app/start.sh

# Use bash to run your script
CMD ["/bin/bash", "./start.sh"]
