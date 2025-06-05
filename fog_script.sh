#!/bin/bash

# Update package list
sudo apt update

# Install system dependencies
sudo apt install -y nodejs npm espeak-ng build-essential

# Install edge-tts globally
sudo npm install -g edge-tts

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull the required model
ollama pull deepseek-r1:1.5b

# Install Python packages
pip install -r fog_requirements.txt