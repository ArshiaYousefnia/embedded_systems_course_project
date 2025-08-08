import socket
import pyaudio
import json
import os
import audioop
import webrtcvad
from vosk import Model, KaldiRecognizer, SetLogLevel
import logging
from configparser import ConfigParser
import time

# --- Setup Logging and Configuration ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

config = ConfigParser()
config.read("client_config.ini")

# Audio settings
SAMPLE_RATE = config.getint("audio", "sample_rate", fallback=16000)
CHANNELS = config.getint("audio", "channels", fallback=1)
FORMAT = pyaudio.paInt16
FRAMES_PER_BUFFER = config.getint("audio", "frames_per_buffer", fallback=4096)
VAD_MODE = config.getint("audio", "vad_mode", fallback=2)
INPUT_DEVICE_INDEX = config.getint("audio", "input_device_index", fallback=4)
SILENCE_THRESHOLD = config.getint("audio", "silence_threshold", fallback=500)

# Network settings
FOG_IP = config.get("network", "fog_ip", fallback="127.0.0.1")
FOG_PORT = config.getint("network", "fog_port", fallback=5050)

# NEW: Command keywords from config
COMMANDS = {
    "CHANGE_LANG_EN": config.get("commands", "change_lang_en", fallback="زبان را به انگلیسی تغییر بده"),
    "CHANGE_LANG_FA": config.get("commands", "change_lang_fa", fallback="change language to persian"),
    "MODE_ONLINE": config.get("commands", "mode_online", fallback="switch to online mode"),
    "MODE_OFFLINE": config.get("commands", "mode_offline", fallback="switch to offline mode"),
}

SetLogLevel(-1)
os.environ["PYTHONWARNINGS"] = "ignore"

# --- Global State Variables ---
# NEW: We need global variables to manage the state that can change at runtime
current_language = config.get("audio", "preferred_language", fallback="en")
model = None
recognizer = None


class AudioPreprocessor:
    def __init__(self):
        self.vad = webrtcvad.Vad(VAD_MODE)
        self.sample_rate = SAMPLE_RATE

    def is_speech(self, frame):
        try:
            return self.vad.is_speech(frame, self.sample_rate)
        except Exception as e:
            logger.error(f"VAD error: {e}")
            return False

    def normalize_audio(self, frame):
        try:
            max_amplitude = audioop.max(frame, 2)
            return audioop.mul(frame, 2, min(32767 // max(1, max_amplitude), 2))
        except Exception as e:
            logger.error(f"Normalization error: {e}")
            return frame

    def reduce_noise(self, frame):
        try:
            audio = bytearray(frame)
            for i in range(0, len(audio), 2):
                sample = int.from_bytes(audio[i:i + 2], "little", signed=True)
                if abs(sample) < SILENCE_THRESHOLD:
                    sample = 0
                audio[i:i + 2] = sample.to_bytes(2, "little", signed=True)
            return bytes(audio)
        except Exception as e:
            logger.error(f"Noise reduction error: {e}")
            return frame


# NEW: Function to load/reload models, now takes language as an argument
def load_and_init_recognizer(language):
    global model, recognizer
    model_paths = {
        "fa": "models/vosk-model-fa-0.5",
        "en": "models/vosk-model-small-en-us-0.15"
    }
    path = model_paths.get(language, model_paths["en"])

    if os.path.exists(path):
        logger.info(f"Loading model for language '{language}' from: {path}")
        model = Model(path)
        recognizer = KaldiRecognizer(model, SAMPLE_RATE)
        logger.info(f"Model for '{language}' loaded successfully.")
        return True

    logger.error(f"Model path not found for language '{language}': {path}")
    return False


def play_feedback(sound_file):
    """Plays a sound file to give feedback to the user."""
    if os.path.exists(sound_file):
        os.system(f"ffplay -nodisp -autoexit -loglevel quiet {sound_file}")
    else:
        logger.warning(f"Feedback sound file not found: {sound_file}")


def send_command_to_fog(command_payload):
    """Sends a command to the fog server."""
    try:
        with socket.create_connection((FOG_IP, FOG_PORT), timeout=10) as sock:
            sock.sendall(json.dumps(command_payload).encode("utf-8"))
            # Wait for response and play it
            with open("response.mp3", "wb") as f:
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    f.write(chunk)
            play_feedback("response.mp3")
            os.remove("response.mp3")
            logger.info("Client Ready. Speak clearly...")
    except Exception as e:
        logger.error(f"Failed to send command to fog: {e}")


def main():
    global current_language, recognizer

    if not load_and_init_recognizer(current_language):
        return

    audio_processor = AudioPreprocessor()
    p = pyaudio.PyAudio()
    stream = None

    try:
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            input_device_index=INPUT_DEVICE_INDEX,
            frames_per_buffer=FRAMES_PER_BUFFER
        )
        logger.info(f"Client Ready (Language: {current_language.upper()}). Speak clearly...")

        while True:
            data = stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)
            processed_data = audio_processor.reduce_noise(data)
            processed_data = audio_processor.normalize_audio(processed_data)

            if recognizer.AcceptWaveform(processed_data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip().lower()

                if not text:
                    continue

                logger.info(f"You said: {text}")

                # --- NEW: Command Handling Logic ---
                new_lang = None
                if text == COMMANDS["CHANGE_LANG_EN"] and current_language != "en":
                    new_lang = "en"
                elif text == COMMANDS["CHANGE_LANG_FA"] and current_language != "fa":
                    new_lang = "fa"

                if new_lang:
                    logger.info(f"Switching language to {new_lang.upper()}...")
                    current_language = new_lang
                    load_and_init_recognizer(current_language)  # Reload model
                    # You should have sound files like 'lang_en.mp3' and 'lang_fa.mp3'
                    play_feedback(f"lang_{current_language}.mp3")
                    logger.info(f"Client Ready (Language: {current_language.upper()}). Speak clearly...")
                    continue  # Skip sending this command to fog

                elif text == COMMANDS["MODE_ONLINE"]:
                    send_command_to_fog({"type": "command", "command": "set_mode", "value": "online"})
                    continue

                elif text == COMMANDS["MODE_OFFLINE"]:
                    send_command_to_fog({"type": "command", "command": "set_mode", "value": "offline"})
                    continue
                # --- End of Command Handling ---

                # If not a command, process as a normal query
                try:
                    # Send as JSON to make the protocol consistent
                    payload = {"type": "query", "text": text}
                    with socket.create_connection((FOG_IP, FOG_PORT), timeout=60) as sock:
                        sock.sendall(json.dumps(payload).encode("utf-8"))
                        with open("response.mp3", "wb") as f:
                            while True:
                                chunk = sock.recv(4096)
                                if not chunk:
                                    break
                                f.write(chunk)
                        play_feedback("response.mp3")
                        os.remove("response.mp3")
                    logger.info("Client Ready. Speak clearly...")
                except socket.error as e:
                    logger.error(f"Network error: {e}")
                except Exception as e:
                    logger.error(f"Error processing response: {e}")
    finally:
        if stream:
            stream.stop_stream()
            stream.close()
        p.terminate()
        logger.info("Audio resources cleaned up.")


if __name__ == "__main__":
    main()