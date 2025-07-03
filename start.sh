#!/usr/bin/env bash
set -e

echo "🎯 Installing Playwright browsers and dependencies..."
playwright install --with-deps

echo "✅ Starting background worker..."
python main.py

