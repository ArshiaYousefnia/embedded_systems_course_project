import socket
import pyaudio
import json
import os
from vosk import Model, KaldiRecognizer, SetLogLevel
import logging
from configparser import ConfigParser
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

config = ConfigParser()
config.read("client_config.ini")

SAMPLE_RATE = config.getint("audio", "sample_rate", fallback=48480)
CHANNELS = 1
FORMAT = pyaudio.paInt16
FRAMES_PER_BUFFER = config.getint("audio", "frames_per_buffer", fallback=1000000)
INPUT_DEVICE_INDEX = config.getint("audio", "input_device_index", fallback=1)

FOG_IP = config.get("network", "fog_ip", fallback="127.0.0.1")
FOG_PORT = config.getint("network", "fog_port", fallback=5050)

COMMANDS = {
    "CHANGE_LANG_EN": config.get("commands", "change_lang_en", fallback="زبان را به انگلیسی تغییر بده"),
    "CHANGE_LANG_FA": config.get("commands", "change_lang_fa", fallback="change language to persian"),
    "MODE_ONLINE_EN": config.get("commands", "mode_online_en", fallback="online mode"),
    "MODE_ONLINE_FA": config.get("commands", "mode_online_fa", fallback="حالت آنلاین"),
    "MODE_OFFLINE_EN": config.get("commands", "mode_offline_en", fallback="offline mode"),
    "MODE_OFFLINE_FA": config.get("commands", "mode_offline_fa", fallback="حالت آفلاین"),
}

SetLogLevel(-1)
os.environ["PYTHONWARNINGS"] = "ignore"

current_language = config.get("audio", "preferred_language", fallback="en")
model = None
recognizer = None

SILENCE_THRESHOLD = config.getfloat("audio", "silence_threshold", fallback=500.0)
SILENCE_DURATION = config.getfloat("audio", "silence_duration", fallback=1.5)

def load_and_init_recognizer(language):
    global model, recognizer
    model_paths = {
        "fa": "models/vosk-model-small-fa-0.5",
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
    if os.path.exists(sound_file):
        os.system(f"ffplay -nodisp -autoexit -loglevel quiet {sound_file}")
    else:
        logger.warning(f"Feedback sound file not found: {sound_file}")

def send_command_to_fog(command_payload):
    try:
        with socket.create_connection((FOG_IP, FOG_PORT), timeout=10) as sock:
            sock.sendall(json.dumps(command_payload).encode("utf-8"))
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

def rms(data):
    shorts = np.frombuffer(data, dtype=np.int16)
    return np.sqrt(np.mean(shorts.astype(np.float32) ** 2))

def main():
    global current_language, recognizer

    if not load_and_init_recognizer(current_language):
        return

    p = pyaudio.PyAudio()
    stream = None

    SILENCE_CHUNK_SIZE = 256
    recognizer_buffer_size = FRAMES_PER_BUFFER

    try:
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            input_device_index=INPUT_DEVICE_INDEX,
            frames_per_buffer=SILENCE_CHUNK_SIZE
        )
        logger.info(f"Client Ready (Language: {current_language.upper()}). Speak clearly...")

        audio_buffer = bytearray()
        recognizer_buffer = bytearray()
        silence_chunks = 0
        silence_chunk_count = int(SILENCE_DURATION * SAMPLE_RATE / SILENCE_CHUNK_SIZE)

        while True:
            data = stream.read(SILENCE_CHUNK_SIZE, exception_on_overflow=False)
            audio_buffer.extend(data)
            recognizer_buffer.extend(data)
            if rms(data) < SILENCE_THRESHOLD:
                silence_chunks += 1
            else:
                silence_chunks = 0
            if (len(recognizer_buffer) >= recognizer_buffer_size or silence_chunks >= silence_chunk_count) \
                and recognizer.AcceptWaveform(bytes(recognizer_buffer)):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip().lower()
                audio_buffer.clear()
                recognizer_buffer.clear()
                silence_chunks = 0
                if not text:
                    continue
                logger.info(f"You said: {text}")
                new_lang = None
                if text == COMMANDS["CHANGE_LANG_EN"] and current_language != "en":
                    new_lang = "en"
                elif text == COMMANDS["CHANGE_LANG_FA"] and current_language != "fa":
                    new_lang = "fa"
                if new_lang:
                    logger.info(f"Switching language to {new_lang.upper()}...")
                    current_language = new_lang
                    load_and_init_recognizer(current_language)
                    play_feedback(f"lang_{current_language}.mp3")
                    logger.info(f"Client Ready (Language: {current_language.upper()}). Speak clearly...")
                    continue
                elif text == COMMANDS["MODE_ONLINE_EN"] or text == COMMANDS["MODE_ONLINE_FA"]:
                    send_command_to_fog({"type": "command", "command": "set_mode", "value": "online"})
                    continue
                elif text == COMMANDS["MODE_OFFLINE_EN"] or text == COMMANDS["MODE_OFFLINE_FA"]:
                    send_command_to_fog({"type": "command", "command": "set_mode", "value": "offline"})
                    continue

                try:
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
