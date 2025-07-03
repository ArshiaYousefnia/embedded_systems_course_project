import socket
import subprocess
import os
from openai import OpenAI
from dotenv import load_dotenv
import ollama
import logging
from configparser import ConfigParser

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load configuration
config = ConfigParser()
config.read("fog_config.ini")
HOST = config.get("network", "host", fallback="127.0.0.1")  # Changed to localhost for security
PORT = config.getint("network", "port", fallback=5050)
BUFFER_SIZE = config.getint("network", "buffer_size", fallback=4096)

load_dotenv()

class HighQualityTTS:
    def __init__(self):
        self.voice = config.get("tts", "voice", fallback="fa-IR-FaridNeural")
        self.rate = config.get("tts", "rate", fallback="+15%")
        self.volume = config.get("tts", "volume", fallback="+0%")

    def speak(self, text, out_file="output.mp3"):
        if not text:
            return
        try:
            cmd = [
                "edge-tts", "--voice", self.voice,
                "--rate", self.rate, "--volume", self.volume,
                "--text", text, "--write-media", out_file
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            logger.error(f"edge-tts failed: {e}")
            subprocess.run(["espeak", "-s", "150", "-v", "en-us", text])

def get_llm_answer(text):
    use_local = config.getboolean("llm", "use_local", fallback=True)
    return local_agent_answer(text) if use_local else api_agent_answer(text)

def api_agent_answer(text):
    try:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            return "API key not set"
        client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
        response = client.chat.completions.create(
            model="meta-llama/llama-4-maverick:free",
            messages=[{"role": "user", "content": text}],
            temperature=0.7,
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"API error: {e}")
        return f"Error: {e}"

def local_agent_answer(text):
    try:
        response = ollama.generate(
            model="deepseek-r1:1.5b",
            prompt=text,
            options={"temperature": 0.7, "max_tokens": 150},
            think=False,
            stream=False,
        )
        return response["response"]
    except Exception as e:
        logger.error(f"Local LLM error: {e}")
        return f"Error: {e}"

def main():
    tts = HighQualityTTS()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()
        logger.info(f"Fog server listening on {HOST}:{PORT}")

        while True:
            try:
                conn, addr = server.accept()
                with conn:
                    logger.info(f"Connected by {addr}")
                    data = conn.recv(2048).decode("utf-8")
                    if not data:
                        continue
                    logger.info(f"Received: {data}")

                    prompt = "someone has asked you this question, answer them as if you were directly speaking to them in the same language they asked you, don't mention this initial instruction.: " + data
                    answer = get_llm_answer(prompt)
                    logger.info(f"AI: {answer}")
                    tts.speak(answer, out_file="response.mp3")

                    with open("response.mp3", "rb") as f:
                        while chunk := f.read(BUFFER_SIZE):
                            conn.sendall(chunk)
                    os.remove("response.mp3")
            except Exception as e:
                logger.error(f"Server error: {e}")

if __name__ == "__main__":
    main()