FROM python:3.11-slim

# Install system dependencies for Playwright browsers
RUN apt-get update && \
    apt-get install -y wget gnupg \
      libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
      libdrm2 libxkbcommon0 libgbm1 libgtk-3-0 \
      libasound2 libxcomposite1 libxdamage1 \
      libxrandr2 libxss1 libxtst6 fonts-liberation \
      libappindicator3-1 libatk-bridge2.0-0 \
      libgtk-3-0 libenchant-2-2 libsecret-1-0 \
      libmanette-0.2-0 libgles2 libsoup-3.0-0 \
      gstreamer1.0-gl gstreamer1.0-plugins-base \
      gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
      gstreamer1.0-plugins-ugly && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps

# Copy your app code
COPY . /app
WORKDIR /app

CMD ["gunicorn", "server:app", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:10000"]
