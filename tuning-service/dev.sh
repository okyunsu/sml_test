#!/bin/bash

# ESG Fine-tuning Service Development Script
echo "Starting ESG Fine-tuning Service in development mode..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if requirements.txt is newer than last install
if [ requirements.txt -nt venv/pyvenv.cfg ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the service
echo "Starting tuning service on port 8003..."
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload 