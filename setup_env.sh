#!/bin/sh
# Simple virtual environment setup script with basic error handling

VENV_DIR=".ortho-venv"

python3 -m venv "$VENV_DIR"
. "$VENV_DIR"/bin/activate
pip install --upgrade pip
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    echo "requirements.txt not found, skipping dependency install." >&2
fi
