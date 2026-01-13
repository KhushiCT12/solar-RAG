#!/bin/bash
# Setup script for RAG virtual environment

echo "Creating virtual environment '.raaag'..."
python3 -m venv .raaag

echo "Activating virtual environment..."
source .raaag/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing requirements..."
pip install -r requirements.txt

echo "Virtual environment setup complete!"
echo "To activate the environment, run: source .raaag/bin/activate"

