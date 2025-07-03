#!/usr/bin/env bash
set -e

echo '✅ Installing Python dependencies...'
pip install --upgrade pip
pip install -r requirements.txt

echo '✅ Installing Playwright browsers...'
playwright install

echo '✅ Starting background worker...'
python main.py
