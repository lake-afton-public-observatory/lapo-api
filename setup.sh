#!/usr/bin/env bash
set -e

echo "Checking dependencies..."

# Check Node.js
if ! command -v node &> /dev/null; then
  echo "Error: node.js is not installed. Please install it first."
  exit 1
fi

# Check Python 3
if ! command -v python3 &> /dev/null; then
  echo "Error: Python 3 is not installed. Please install it first."
  exit 1
fi

# Set up .env if it doesn't exist
if [ ! -f .env ]; then
  cp .env_example .env
  echo "Created .env from .env_example — fill in your API keys before running."
else
  echo ".env already exists, skipping."
fi

# Install npm dependencies
echo "Installing npm packages..."
npm install

# Install Python dependencies
echo "Installing Python packages..."
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt

echo "Done! Run 'npm start' to start the server."
echo "Once running, visit: http://localhost:${PORT:-3000}"
