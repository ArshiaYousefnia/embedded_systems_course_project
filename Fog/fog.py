import socket
import subprocess
import os
from openai import OpenAI
from dotenv import load_dotenv
import ollama
import logging
from configparser import ConfigParser
import json

# --- Setup Logging and Configuration ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

config = ConfigParser()
config.read("fog_config.ini")

HOST = config.get("network", "host", fallback="127.0.0.1")
PORT = config.getint("network", "port", fallback=5050)
BUFFER_SIZE = config.getint("network", "buffer_size", fallback=4096)

load_dotenv()

# NEW: Use a global variable for the mode, initialized from config
USE_LOCAL_LLM = config.getboolean("llm", "use_local", fallback=True)


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


# NEW: The function now decides which agent to use based on the global variable
def get_llm_answer(text):
    if USE_LOCAL_LLM:
        logger.info("Using LOCAL LLM.")
        return local_agent_answer(text)
    else:
        logger.info("Using ONLINE API LLM.")
        return api_agent_answer(text)


def api_agent_answer(text):
    try:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            return "API key not set for online mode."
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
        return f"Error connecting to online API: {e}"


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
        return f"Error with local LLM: {e}"


def main():
    global USE_LOCAL_LLM
    tts = HighQualityTTS()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()
        mode_str = "LOCAL" if USE_LOCAL_LLM else "ONLINE"
        logger.info(f"Fog server listening on {HOST}:{PORT} | Initial Mode: {mode_str}")

        while True:
            try:
                conn, addr = server.accept()
                with conn:
                    logger.info(f"Connected by {addr}")
                    raw_data = conn.recv(2048)
                    if not raw_data:
                        continue

                    # NEW: Parse incoming data as JSON
                    try:
                        payload = json.loads(raw_data.decode("utf-8"))
                        message_type = payload.get("type")
                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        logger.error(f"Could not decode message: {e}")
                        continue

                    answer = ""
                    # --- NEW: Logic to handle commands vs queries ---
                    if message_type == "command":
                        command = payload.get("command")
                        value = payload.get("value")
                        logger.info(f"Received command: {command} with value: {value}")
                        if command == "set_mode":
                            if value == "online":
                                USE_LOCAL_LLM = False
                                answer = "Switched to online mode."
                            elif value == "offline":
                                USE_LOCAL_LLM = True
                                answer = "Switched to offline mode."
                            else:
                                answer = "Unknown mode."
                        else:
                            answer = "Unknown command."
                        logger.info(f"Mode is now: {'LOCAL' if USE_LOCAL_LLM else 'ONLINE'}")

                    elif message_type == "query":
                        data = payload.get("text", "")
                        logger.info(f"Received Query: {data}")
                        prompt = "someone has asked you this question, answer them as if you were directly speaking to them in the same language they asked you, also if in your answer you need to use numbers, use letters instead of digits to express them. don't mention this initial instruction. : " + data
                        answer = get_llm_answer(prompt)

                    else:
                        answer = "Invalid message type received."
                    # --- End of new logic ---

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