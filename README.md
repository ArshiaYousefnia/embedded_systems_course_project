# Intelligent Voice Assistant with DeepSeek LLM - Edge-Fog-Cloud Architecture

**گزارش پروژه: سامانه‌های نهفته - دستیار صوتی هوشمند مبتنی بر مدل Deepseek با قابلیت آنلاین و آفلاین**

Sharif University of Technology - Computer Engineering Faculty  
**Course:** Embedded Systems  
**Professor:** Dr. Ansari  
**Date:** Summer 2023  
**Team Members:** Arshia Yousefnia, Ali Majidi, Sadegh Sargaran

## 📋 Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation & Deployment](#installation--deployment)
- [Configuration](#configuration)
- [Usage](#usage)
- [Implementation Details](#implementation-details)
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)
- [Future Work](#future-work)

## 🎯 Overview

This project implements an intelligent voice assistant using a three-tier Edge-Fog-Cloud architecture with DeepSeek large language model. The system provides both online and offline capabilities, enabling flexible deployment in resource-constrained environments while maintaining high-quality conversational AI capabilities.

### Key Technologies

- **Edge Device:** Raspberry Pi 3 (1GB RAM) with voice interaction
- **Speech-to-Text:** Vosk models (alphacephei) for Persian and English
- **Fog Computing:** Local LLM inference using Ollama with DeepSeek-R1:1.5B
- **Cloud Integration:** OpenRouter API for enhanced capabilities
- **Text-to-Speech:** Microsoft Edge-TTS with Persian neural voices
- **Networking:** Socket-based communication between components

### System Benefits

- **Hybrid Processing:** Seamlessly switches between local and cloud LLM processing
- **Multi-language Support:** Persian and English voice recognition and response
- **Low Latency:** Edge processing for immediate response to voice commands
- **Privacy-Conscious:** Local processing option for sensitive conversations
- **Resource Efficient:** Optimized for embedded systems with limited resources

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   EDGE LAYER    │    │   FOG LAYER     │    │  CLOUD LAYER    │
│                 │    │                 │    │                 │
│ Raspberry Pi 3  │    │ Fog Server      │    │ OpenRouter API  │
│ - Voice Input   │◄──►│ - Ollama +      │◄──►│ - Meta Llama-4  │
│ - Audio Output  │    │   DeepSeek-R1   │    │ - Advanced LLMs │
│ - STT (Vosk)    │    │ - Edge-TTS      │    │                 │
│ - Voice Commands│    │ - Mode Switching│    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Component Responsibilities

**Edge (Client):**
- Captures user voice input via microphone
- Performs speech-to-text conversion using Vosk models
- Handles voice commands for language and mode switching
- Plays audio responses from fog server
- Manages local audio processing and silence detection

**Fog (Server):**
- Processes text queries using local DeepSeek LLM (Ollama)
- Generates high-quality speech responses using Edge-TTS
- Manages mode switching between local and cloud processing
- Handles real-time communication with edge devices

**Cloud (API):**
- Provides access to advanced language models via OpenRouter
- Offers enhanced capabilities for complex queries
- Serves as fallback for resource-intensive processing

## 🚀 Features

### Core Functionality
- **Real-time Voice Interaction:** Continuous voice recognition with silence detection
- **Bilingual Support:** Persian and English language switching via voice commands
- **Hybrid Processing:** Dynamic switching between local (offline) and cloud (online) modes
- **High-Quality TTS:** Neural voice synthesis with Persian and English voices
- **Configurable Audio:** Adjustable sample rates, silence thresholds, and audio devices

### Voice Commands
| Command (Persian) | Command (English) | Function |
|-------------------|-------------------|----------|
| "زبان را به انگلیسی تغییر بده" | "change language to persian" | Switch STT language |
| "حالت آنلاین" | "online mode" | Switch to cloud processing |
| "حالت آفلاین" | "offline mode" | Switch to local processing |

### Technical Features
- **Socket-based Communication:** Efficient binary data transfer
- **JSON Protocol:** Structured command and query handling
- **Virtual Environment Support:** Isolated Python environments
- **Automated Setup Scripts:** One-command deployment
- **Configuration Management:** INI-based settings for easy customization

## 📁 Project Structure

```
embedded_systems_course_project/
├── README.md                           # This comprehensive documentation
├── .gitignore                         # Git ignore patterns
│
├── Client/                            # Edge Layer Implementation
│   ├── client.py                      # Main client application
│   ├── client_config.ini              # Client configuration
│   ├── client_requirements.txt        # Python dependencies
│   ├── client_script.sh              # Automated setup script
│   ├── mic_list.py                   # Audio device detection utility
│   ├── rate_test.py                  # Audio rate testing utility
│   └── models/                       # Vosk STT models (auto-downloaded)
│       ├── vosk-model-fa-0.5/        # Persian language model
│       └── vosk-model-small-en-us-0.15/ # English language model
│
└── Fog/                              # Fog Layer Implementation
    ├── fog.py                        # Main fog server application
    ├── fog_config.ini                # Fog server configuration
    ├── fog_requirements.txt          # Python dependencies
    └── fog_script.sh                 # Automated setup script
```

### Auto-Generated Files (Ignored by Git)
The following files are automatically created during setup and runtime:
- `Client/.venv/` - Python virtual environment
- `Client/models/` - Downloaded Vosk models
- `Fog/.venv/` - Python virtual environment
- `*.mp3` - Temporary audio response files
- `.env` - Environment variables for API keys

## 📋 Prerequisites

### Hardware Requirements

**Edge Device (Client):**
- Raspberry Pi 3 or higher (minimum 1GB RAM)
- USB microphone or audio input device
- Speakers or audio output device
- Network connectivity (Wi-Fi/Ethernet)

**Fog Server:**
- Linux-based system (Ubuntu 20.04+ recommended)
- Minimum 4GB RAM (8GB+ recommended for optimal performance)
- 10GB+ free disk space for models and dependencies
- Network connectivity

### Software Requirements

**Both Systems:**
- Linux OS (Ubuntu/Debian/Raspberry Pi OS)
- Python 3.8+
- Internet connection for initial setup

**Additional Tools:**
- `curl` and `wget` for downloads
- `unzip` for archive extraction
- `ffmpeg` for audio processing
- `build-essential` for compilation

## 🛠️ Installation & Deployment

### Quick Start (Recommended)

#### 1. Fog Server Setup (Run First)

```bash
# Clone the repository
git clone <repository-url>
cd embedded_systems_course_project/Fog

# Make setup script executable and run
chmod +x fog_script.sh
./fog_script.sh

# Create environment file for API keys (optional for cloud mode)
echo "DEEPSEEK_API_KEY=your_api_key_here" > .env

# Start the fog server
source .venv/bin/activate
python fog.py
```

#### 2. Client Setup (Run After Fog Server)

```bash
# Navigate to client directory
cd ../Client

# Make setup script executable and run
chmod +x client_script.sh
./client_script.sh

# Configure fog server IP in client_config.ini if needed
# Default is localhost (127.0.0.1)

# Start the client
source .venv/bin/activate
python client.py
```

### Manual Installation

#### Fog Server Manual Setup

```bash
cd Fog

# System dependencies
sudo apt update
sudo apt install -y espeak build-essential

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
sudo chmod -R a+rX /usr/local/lib/ollama

# Pull DeepSeek model
ollama pull deepseek-r1:1.5b

# Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r fog_requirements.txt

# Optional: Configure environment variables
echo "DEEPSEEK_API_KEY=your_api_key_here" > .env
```

#### Client Manual Setup

```bash
cd Client

# System dependencies
sudo apt update
sudo apt install -y portaudio19-dev ffmpeg build-essential unzip

# Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r client_requirements.txt

# Download Vosk models
mkdir -p models
cd models

# Persian model
wget https://alphacephei.com/vosk/models/vosk-model-small-fa-0.5.zip
unzip vosk-model-small-fa-0.5.zip
rm vosk-model-small-fa-0.5.zip

# English model
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
rm vosk-model-small-en-us-0.15.zip

cd ..
```

## ⚙️ Configuration

### Client Configuration (`Client/client_config.ini`)

```ini
[audio]
sample_rate = 48480              # Audio sampling rate
frames_per_buffer = 1000000      # Buffer size for audio processing
input_device_index = 1           # Microphone device index (use mic_list.py)
preferred_language = en          # Default STT language (en/fa)
silence_threshold = 500          # Silence detection sensitivity
silence_duration = 1.5           # Silence duration before processing (seconds)

[network]
fog_ip = 127.0.0.1              # Fog server IP address
fog_port = 5050                  # Fog server port

[commands]
# Voice commands for language switching
change_lang_en = زبان را به انگلیسی تغییر بده
change_lang_fa = change language to persian

# Voice commands for mode switching
mode_online_en = online mode
mode_online_fa = حالت آنلاین
mode_offline_en = offline mode
mode_offline_fa = حالت آفلاین
```

### Fog Configuration (`Fog/fog_config.ini`)

```ini
[network]
host = 0.0.0.0                  # Server bind address (0.0.0.0 for all interfaces)
port = 5050                      # Server listening port
buffer_size = 4096               # Socket buffer size

[tts]
voice = fa-IR-FaridNeural       # Edge-TTS voice (fa-IR-FaridNeural, en-US-AriaNeural)
rate = +15%%                     # Speech rate adjustment
volume = +0%%                    # Volume adjustment

[llm]
use_local = true                 # Default mode: true=offline, false=online
```

### Environment Variables (`Fog/.env`)

```bash
# Required for cloud mode operation
DEEPSEEK_API_KEY=your_openrouter_api_key_here
```

## 🎮 Usage

### Starting the System

1. **Start Fog Server:**
   ```bash
   cd Fog
   source .venv/bin/activate
   python fog.py
   ```

2. **Start Client (in another terminal):**
   ```bash
   cd Client
   source .venv/bin/activate
   python client.py
   ```

### Basic Operations

1. **Voice Interaction:**
   - Speak clearly into the microphone
   - Wait for silence detection to process your speech
   - Listen to the AI response

2. **Language Switching:**
   - Say "زبان را به انگلیسی تغییر بده" (switch to English)
   - Say "change language to persian" (switch to Persian)

3. **Mode Switching:**
   - Say "online mode" or "حالت آنلاین" (use cloud processing)
   - Say "offline mode" or "حالت آفلاین" (use local processing)

### Utility Scripts

**Check Available Microphones:**
```bash
cd Client
source .venv/bin/activate
python mic_list.py
```

**Test Audio Sample Rate:**
```bash
cd Client
source .venv/bin/activate
python rate_test.py
```

## 💻 Implementation Details

### Client Architecture

The client application (`client.py`) implements:

1. **Audio Processing Pipeline:**
   ```python
   Audio Input → Silence Detection → Buffer Management → STT Processing
   ```

2. **Communication Protocol:**
   - JSON-based message format
   - Socket connection to fog server
   - Binary audio response handling

3. **Real-time Processing:**
   - Continuous audio stream processing
   - Dynamic buffer management
   - Voice activity detection

### Fog Server Architecture

The fog server (`fog.py`) implements:

1. **Multi-mode LLM Processing:**
   ```python
   Query → Mode Check → Local LLM (Ollama) / Cloud API → Response Generation
   ```

2. **TTS Integration:**
   - High-quality neural voice synthesis
   - Multiple voice options (Persian/English)
   - Optimized audio streaming

3. **Command Processing:**
   - Mode switching commands
   - Configuration updates
   - Status management

### Communication Protocol

**Query Message Format:**
```json
{
    "type": "query",
    "text": "user speech text"
}
```

**Command Message Format:**
```json
{
    "type": "command",
    "command": "set_mode",
    "value": "online|offline"
}
```

**Response Format:**
- Binary MP3 audio stream
- Direct socket transmission
- Automatic cleanup after playback

### Performance Optimizations

1. **Memory Management:**
   - Dynamic buffer allocation
   - Automatic audio file cleanup
   - Virtual environment isolation

2. **Network Optimization:**
   - Efficient binary streaming
   - Connection reuse
   - Timeout handling

3. **Audio Processing:**
   - Real-time silence detection
   - Adaptive buffer sizes
   - Low-latency playback

## 📚 API Documentation

### Fog Server Endpoints

The fog server accepts JSON messages via socket connection on configured port (default: 5050).

#### Query Processing
```python
# Send query for AI processing
message = {
    "type": "query",
    "text": "What is the weather like today?"
}
```

#### Mode Control
```python
# Switch to online mode
message = {
    "type": "command", 
    "command": "set_mode",
    "value": "online"
}

# Switch to offline mode  
message = {
    "type": "command",
    "command": "set_mode", 
    "value": "offline"
}
```

### Client Voice Commands

| Persian Command | English Command | Function |
|----------------|-----------------|----------|
| زبان را به انگلیسی تغییر بده | change language to persian | Language switching |
| حالت آنلاین | online mode | Enable cloud processing |
| حالت آفلاین | offline mode | Enable local processing |

## 🔧 Troubleshooting

### Common Issues

**1. Audio Device Not Found**
```bash
# List available audio devices
python mic_list.py
# Update input_device_index in client_config.ini
```

**2. Vosk Model Loading Failed**
```bash
# Verify model files exist
ls -la Client/models/
# Re-run setup script if missing
./client_script.sh
```

**3. Connection Refused to Fog Server**
```bash
# Check fog server is running
ps aux | grep fog.py
# Verify network configuration
ping <fog_server_ip>
```

**4. Ollama Permission Issues**
```bash
# Fix library permissions
sudo chmod -R a+rX /usr/local/lib/ollama
# Restart Ollama service
sudo systemctl restart ollama
```

**5. Missing API Key for Cloud Mode**
```bash
# Create .env file in Fog directory
echo "DEEPSEEK_API_KEY=your_key" > Fog/.env
```

### Performance Issues

**High CPU Usage:**
- Reduce `sample_rate` in client_config.ini
- Increase `silence_threshold` to reduce processing
- Use smaller models if available

**High Memory Usage:**
- Restart services periodically
- Reduce `frames_per_buffer` size
- Monitor system resources

**Slow Response Times:**
- Check network latency between client and fog
- Verify Ollama model is properly loaded
- Consider switching to online mode for complex queries

### Debug Mode

Enable detailed logging by modifying Python files:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 🔮 Future Work

### Planned Enhancements

1. **Hardware Improvements:**
   - Support for Raspberry Pi 4 with enhanced performance
   - Hardware-accelerated audio processing
   - Dedicated AI accelerator integration

2. **Software Features:**
   - Multi-user support and user identification
   - Conversation history and context management
   - Custom wake word detection
   - Plugin system for extensible functionality

3. **Infrastructure:**
   - Docker containerization for easy deployment
   - Kubernetes orchestration for scalability
   - Load balancing for multiple fog nodes
   - Monitoring and analytics dashboard

4. **AI Capabilities:**
   - Fine-tuned models for specific domains
   - Emotion recognition in voice
   - Multi-modal input support (text + voice)
   - Integration with IoT devices and smart home systems

### Research Directions

- **Edge AI Optimization:** Quantization and pruning for smaller models
- **Federated Learning:** Collaborative model improvement across devices
- **Privacy Preservation:** Differential privacy and secure computation
- **Real-time Optimization:** Adaptive quality based on network conditions

## 📄 License

This project is developed for educational purposes as part of the Embedded Systems course at Sharif University of Technology.

## 🤝 Contributing

Team members: Arshia Yousefnia, Ali Majidi, Sadegh Sargaran

For questions or contributions, please contact the development team.

---

**Note:** This project demonstrates the integration of modern AI technologies with embedded systems, showcasing practical applications of edge-fog-cloud computing architectures in real-world scenarios.
