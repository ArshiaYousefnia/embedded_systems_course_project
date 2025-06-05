import socket
import pyaudio
import json
import os
import audioop
import webrtcvad
from vosk import Model, KaldiRecognizer, SetLogLevel
import logging
from configparser import ConfigParser

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load configuration
config = ConfigParser()
config.read("client_config.ini")
SAMPLE_RATE = config.getint("audio", "sample_rate", fallback=16000)
CHANNELS = config.getint("audio", "channels", fallback=1)
FORMAT = pyaudio.paInt16
FRAMES_PER_BUFFER = config.getint("audio", "frames_per_buffer", fallback=4096)
VAD_MODE = config.getint("audio", "vad_mode", fallback=2)
INPUT_DEVICE_INDEX = config.getint("audio", "input_device_index", fallback=4)
SILENCE_THRESHOLD = config.getint("audio", "silence_threshold", fallback=500)
FOG_IP = config.get("network", "fog_ip", fallback="192.168.1.100")
FOG_PORT = config.getint("network", "fog_port", fallback=5050)

SetLogLevel(-1)
os.environ["PYTHONWARNINGS"] = "ignore"

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
                sample = int.from_bytes(audio[i:i+2], "little", signed=True)
                if abs(sample) < SILENCE_THRESHOLD:
                    sample = 0
                audio[i:i+2] = sample.to_bytes(2, "little", signed=True)
            return bytes(audio)
        except Exception as e:
            logger.error(f"Noise reduction error: {e}")
            return frame

def load_model(preferred_language="fa"):
    model_paths = {
        "fa": "models/vosk-model-fa-0.5",
        "en": "models/vosk-model-small-en-us-0.15"
    }
    path = model_paths.get(preferred_language, model_paths["en"])
    if os.path.exists(path):
        logger.info(f"Loaded model from: {path}")
        return Model(path)
    logger.error("No suitable model found.")
    return None

def main():
    model = load_model()
    if not model:
        return

    recognizer = KaldiRecognizer(model, SAMPLE_RATE)
    audio_processor = AudioPreprocessor()
    p = pyaudio.PyAudio()

    try:
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            input_device_index=INPUT_DEVICE_INDEX,
            frames_per_buffer=FRAMES_PER_BUFFER
        )
        logger.info("Client Ready. Speak clearly...")

        while True:
            data = stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)
            data = audio_processor.reduce_noise(data)
            data = audio_processor.normalize_audio(data)

            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip()
                if text:
                    logger.info(f"You said: {text}")
                    try:
                        with socket.create_connection((FOG_IP, FOG_PORT), timeout=10) as sock:
                            sock.sendall(text.encode("utf-8"))
                            with open("response.mp3", "wb") as f:
                                while True:
                                    chunk = sock.recv(4096)
                                    if not chunk:
                                        break
                                    f.write(chunk)
                        os.system("ffplay -nodisp -autoexit -loglevel quiet response.mp3")
                        os.remove("response.mp3")
                    except socket.error as e:
                        logger.error(f"Network error: {e}")
                    except Exception as e:
                        logger.error(f"Error processing response: {e}")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        logger.info("Audio resources cleaned up.")

if __name__ == "__main__":
    main()