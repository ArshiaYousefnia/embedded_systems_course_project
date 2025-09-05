import pyaudio

p = pyaudio.PyAudio()
device = 1  # your USB mic index
for rate in (8000, 16000, 32000, 44100, 48000, 48480, 96000):
    try:
        p.is_format_supported(
            rate,
            input_device=device,
            input_channels=1,
            input_format=pyaudio.paInt16
        )
        print(f"{rate} Hz ✔ supported")
    except Exception:
        print(f"{rate} Hz ✘ not supported")
p.terminate()
