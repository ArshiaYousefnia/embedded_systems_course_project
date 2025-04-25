import time
import pyaudio
import numpy as np
from vosk import Model, KaldiRecognizer, SetLogLevel
import os
import sys
import subprocess
from openai import OpenAI
from dotenv import load_dotenv
import webrtcvad
import ollama
import audioop
import json

# Disable all unnecessary logs
SetLogLevel(-1)
os.environ['PYTHONWARNINGS'] = 'ignore'

# Enhanced Audio Configuration
AUDIO_FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_RATE = 16000
FRAMES_PER_BUFFER = 4096
INPUT_DEVICE_INDEX = 4  # Using sysdefault as per your list
SILENCE_THRESHOLD = 500


class AudioPreprocessor:
    """Handles audio preprocessing for better recognition"""

    def __init__(self):
        self.vad = webrtcvad.Vad(2)
        self.sample_rate = SAMPLE_RATE
        self.frame_size = int(self.sample_rate * 0.03)  # 30ms frames

    def is_speech(self, audio_frame):
        """Detect if frame contains speech using WebRTC VAD"""
        try:
            return self.vad.is_speech(audio_frame, self.sample_rate)
        except:
            return False

    def normalize_audio(self, audio_frame):
        """Normalize audio volume"""
        try:
            return audioop.mul(audio_frame, 2,
                               min(32767 // max(1, audioop.max(audio_frame, 2)), 2))
        except:
            return audio_frame

    def reduce_noise(self, audio_frame):
        """Simple noise reduction that creates a new numpy array"""
        try:
            audio_data = np.frombuffer(audio_frame, dtype=np.int16).copy()  # Create a writable copy
            audio_data[np.abs(audio_data) < SILENCE_THRESHOLD] = 0
            return audio_data.tobytes()
        except:
            return audio_frame


class HighQualityTTS:
    def __init__(self):
        #self.voice = "en-US-JennyNeural"
        self.voice = "fa-IR-FaridNeural"
        self.rate = "+15%"
        self.volume = "+0%"

    def speak(self, text):
        if not text:
            return

        try:
            cmd = [
                "edge-tts",
                "--voice", self.voice,
                "--rate", self.rate,
                "--volume", self.volume,
                "--text", text,
                "--write-media", "output.mp3"
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            subprocess.run([
                "ffplay",
                "-nodisp",
                "-autoexit",
                "-loglevel", "quiet",
                "output.mp3"
            ], stderr=subprocess.DEVNULL)
            os.remove("output.mp3")

        except Exception as e:
            print(f"TTS Error: {e}")
            subprocess.run(["espeak", "-s", "150", "-v", "en-us", text])


def get_llm_answer(text: str) -> str:
    use_local = True

    return local_agent_answer(text) if use_local else api_agent_answer(text)


def api_agent_answer(text: str) -> str:
    try:
        load_dotenv()
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            return "API key not configured"

        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )

        response = client.chat.completions.create(
            #model="nvidia/llama-3.1-nemotron-nano-8b-v1:free",
            model="meta-llama/llama-4-maverick:free",
            messages=[{"role": "user", "content": "someone has asked you this question, answer them as if you were directly speaking to them in the same langusage they asked you, don't mention this initial instruction.: " + text}],
            temperature=0.7,
            max_tokens=150
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error: {str(e)}"

def local_agent_answer(text: str) -> str:
    try:
        model_name = "deepseek-r1:1.5b"
        prompt = "someone has asked you this question, answer them as if you were directly speaking to them in the same language they asked you, don't mention this initial instruction.: " + text

        response = ollama.generate(
            model=model_name,
            prompt=prompt,
            options={
                "temperature": 0.7,
                "max_tokens": 150
            }
        )

        return response['response']

    except Exception as e:
        return f"Error: {str(e)}"


def setup_audio_stream(p):
    """Handle audio stream setup with error recovery"""
    for attempt in range(3):
        try:
            dev_info = p.get_device_info_by_index(INPUT_DEVICE_INDEX)
            print(f"\nUsing audio device: {dev_info['name']}")

            stream = p.open(
                format=AUDIO_FORMAT,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                input_device_index=INPUT_DEVICE_INDEX,
                frames_per_buffer=FRAMES_PER_BUFFER,
                start=False
            )

            # Test if the stream works
            stream.start_stream()
            stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)
            return stream

        except Exception as e:
            print(f"Audio setup attempt {attempt + 1} failed: {str(e)}")
            if attempt == 2:
                raise
            time.sleep(1)


def main():
    # Try to load the best available model
    model_paths = [
        "models/vosk-model-fa-0.5",
        #"models/vosk-model-small-fa-0.42",
        #"models/vosk-model-en-us-0.22-lgraph",
        "models/vosk-model-small-en-us-0.15",
    ]

    model = None
    for path in model_paths:
        if os.path.exists(path):
            try:
                model = Model(path)
                print(f"Loaded model from: {path}")
                break
            except:
                continue

    if not model:
        print("\nError: No suitable Vosk model found. Please download one:")
        print("Small model: wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip")
        print("Large model: wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.42-gigaspeech.zip")
        sys.exit(1)

    recognizer = KaldiRecognizer(model, SAMPLE_RATE)
    tts = HighQualityTTS()
    audio_processor = AudioPreprocessor()

    try:
        p = pyaudio.PyAudio()
        stream = setup_audio_stream(p)

        print("\nSystem ready. Speak clearly into your microphone (Press Ctrl+C to stop)...")
        print("Listening...", end="", flush=True)

        while True:
            try:
                data = stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)

                # Process audio in a safe way
                processed_data = audio_processor.reduce_noise(data)
                processed_data = audio_processor.normalize_audio(processed_data)

                if recognizer.AcceptWaveform(processed_data):
                    result = json.loads(recognizer.Result())
                    text = result.get('text', '').strip()
                    if text:
                        print(f"\nYou said: {text}")
                        answer = get_llm_answer(text)
                        print(f"AI: {answer}")
                        tts.speak(answer)
                        print("\nListening...", end="", flush=True)

                partial = json.loads(recognizer.PartialResult())
                partial_text = partial.get('partial', '').strip()
                if partial_text:
                    print(f"\rListening: {partial_text.ljust(50)}", end="", flush=True)

            except IOError as e:
                print(f"\nAudio error: {e}. Reconnecting...")
                stream.close()
                time.sleep(1)
                stream = setup_audio_stream(p)
            except Exception as e:
                print(f"\nUnexpected error: {e}")
                break

    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"\nFatal error: {e}")
    finally:
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()
        p.terminate()


if __name__ == "__main__":
    # Suppress ALSA/JACK warnings
    os.environ['PYTHONWARNINGS'] = 'ignore'

    print("Speech Recognition System - Improved Version")
    print("Suppressing ALSA/JACK warnings for cleaner output...")

    main()