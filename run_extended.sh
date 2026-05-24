#!/bin/bash

# Path to the virtual environment
VENV_PATH="./venv"

# Check if venv exists, if not, create it and install deps (failsafe)
if [ ! -d "$VENV_PATH" ]; then
    echo "Virtual environment not found. Setting it up..."
    python3 -m venv venv
    source venv/bin/activate
    pip install mido python-rtmidi customtkinter pillow
else
    source venv/bin/activate
fi

# Run the MIDI engine
echo "Starting PyMixensia MIDI Engine (EXTENDED)..."
python3 mixensia_engine_extended.py
