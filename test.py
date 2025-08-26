
import sounddevice as sd
import numpy as np

duration = 0.5

def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    print(indata)

with sd.InputStream(callback=audio_callback, channels=1, samplerate=44100, blocksize=int(44100 * duration)):
    print("Recording... Press Ctrl+C to stop.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Stopped recording.")
