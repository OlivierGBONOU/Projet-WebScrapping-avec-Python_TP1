FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances système nécessaires pour Chrome et Chromedriver
RUN apt-get update && apt-get install -y \
    gnupg \
    wget \
    unzip \
    curl \
    libglib2.0-0 \
    libnss3 \
    libfontconfig1 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxtst6 \
    ca-certificates \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libgcc1 \
    libstdc++6 \
    xdg-utils \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Installation de Chrome et Chromedriver depuis Chrome for Testing
RUN curl -s https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json > /tmp/versions.json \
    && latest_version=$(jq -r '.channels.Stable.version' /tmp/versions.json) \
    && CHROME_URL="https://storage.googleapis.com/chrome-for-testing-public/${latest_version}/linux64/chrome-linux64.zip" \
    && wget -q --continue -O /tmp/chrome.zip "$CHROME_URL" \
    && unzip /tmp/chrome.zip -d /opt/chrome \
    && chmod +x /opt/chrome/chrome-linux64/chrome \
    && CHROMEDRIVER_URL="https://storage.googleapis.com/chrome-for-testing-public/${latest_version}/linux64/chromedriver-linux64.zip" \
    && wget -q --continue -O /tmp/chromedriver.zip "$CHROMEDRIVER_URL" \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && mv /usr/local/bin/chromedriver-linux64/chromedriver /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf /tmp/chromedriver.zip /tmp/chrome.zip /tmp/versions.json /usr/local/bin/chromedriver-linux64

# Copie des fichiers du projet
COPY . .

# Assurez-vous que le dossier static est bien copié
COPY static/ /app/static/

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Exposition du port de Flask
EXPOSE 8000

# Commande pour démarrer l'application
CMD ["python", "app.py"]