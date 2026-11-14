#!/bin/bash
# Unk Agent CLI Launcher

# Ensure venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Check for core dependency to see if installation is needed
if ! pip freeze | grep -q "google-genai"; then
    echo "First run detected. Installing dependencies..."
    pip install -r requirements.txt
fi

export GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT:-mineral-subject-487519-v6}

# Run the CLI
python cli.py