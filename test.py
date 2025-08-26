
from collections import deque
import sounddevice as sd
import numpy as np

duration = 0.5

def audio_callback(indata, frames, time, status):
    if status:
        print(status)

    # print(indata) # Raw audio data

    # Use Root of Mean Square to create a single value for volume that emphasizes louder sounds
    rms = np.sqrt(np.mean(indata**2))

with sd.InputStream(callback=audio_callback, channels=1, samplerate=44100, blocksize=int(44100 * duration)):
    print("Recording... Press Ctrl+C to stop.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Stopped recording.")
