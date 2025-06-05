#!/bin/bash

# Exit on error
set -e

# Update package list
echo "Updating package list..."
sudo apt update

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install -y portaudio19-dev ffmpeg build-essential unzip

# Install Python packages from requirements.txt
echo "Installing Python dependencies..."
pip install -r client_requirements.txt

# Define Vosk model URLs and paths
MODELS_DIR="models"
VOSK_MODELS=(
  "vosk-model-fa-0.5:https://alphacephei.com/vosk/models/vosk-model-fa-0.5.zip"
  "vosk-model-small-en-us-0.15:https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
)

# Create models directory if it doesn't exist
mkdir -p "$MODELS_DIR"

# Download and extract Vosk models if not present
for model in "${VOSK_MODELS[@]}"; do
  MODEL_NAME=$(echo "$model" | cut -d':' -f1)
  MODEL_URL=$(echo "$model" | cut -d':' -f2)
  MODEL_PATH="$MODELS_DIR/$MODEL_NAME"

  if [ -d "$MODEL_PATH" ]; then
    echo "Model $MODEL_NAME already exists in $MODEL_PATH"
  else
    echo "Downloading $MODEL_NAME from $MODEL_URL..."
    wget -P "$MODELS_DIR" "$MODEL_URL"
    echo "Extracting $MODEL_NAME..."
    unzip "$MODELS_DIR/$MODEL_NAME.zip" -d "$MODELS_DIR"
    rm "$MODELS_DIR/$MODEL_NAME.zip"
    echo "Model $MODEL_NAME extracted to $MODEL_PATH"
  fi
done

echo "Client setup complete."