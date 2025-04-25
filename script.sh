#!/bin/bash

# Update package lists
sudo apt-get update

# Install system dependencies
sudo apt-get install -y \
    ffmpeg \
    espeak \
    portaudio19-dev \
    python3-dev \
    python3-pip

# Create models directory if it doesn't exist
mkdir -p models

# Download and extract Vosk models
curl -SL https://alphacephei.com/vosk/models/vosk-model-fa-0.5.zip -o vosk-model-fa-0.5.zip
unzip vosk-model-fa-0.5.zip -d models/
mv models/vosk-model-fa-0.5 models/vosk-model-fa-0.5
rm vosk-model-fa-0.5.zip

curl -SL https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip -o vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip -d models/
mv models/vosk-model-small-en-us-0.15 models/vosk-model-small-en-us-0.15
rm vosk-model-small-en-us-0.15.zip

# Install Ollama application if not already installed
if ! command -v ollama &> /dev/null
then
    echo "Installing Ollama..."
    curl https://ollama.ai/install.sh | sh
fi

# Install Python dependencies
pip3 install -r requirements.txt

echo "Installation complete. Please set up your .env file with:"
echo "DEEPSEEK_API_KEY=your_api_key_here"
echo "fro local agent run ollama before hand"