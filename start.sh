#!/usr/bin/env bash
set -e

echo '?? Installing Playwright browsers...'
playwright install

echo '?? Starting your Python app...'
python youtube_upload.py
