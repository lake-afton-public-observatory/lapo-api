#!/usr/bin/env bash
set -e

echo "Checking dependencies..."

if ! command -v python3 &> /dev/null; then
  echo "Error: Python 3 is not installed. Please install it first."
  exit 1
fi

if [ ! -f .env ]; then
  cp .env_example .env
  echo "Created .env from .env_example — fill in your API keys before running."
else
  echo ".env already exists, skipping."
fi

echo "Installing Python packages..."
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt

echo "Done! Run 'uvicorn app.main:app --reload' to start the server."
