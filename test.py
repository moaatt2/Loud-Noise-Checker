
from collections import deque
import sounddevice as sd
import numpy as np

# Smoothing factor for expoential moving average
alpha = 0.03

# How many seconds of audio in each sample
duration = 0.5

# Set how many samples to keep in memory
num_samples = 25

# Instantiate a double ended queue to hold samples
samples = deque(maxlen=num_samples)


def audio_callback(indata, frames, time, status):
    if status:
        print(status)

    # print(indata) # Raw audio data

    # Use Root of Mean Square to create a single value for volume that emphasizes louder sounds
    rms = np.sqrt(np.mean(indata**2))

    # Calcualte EMA if enough samples are present
    if len(samples) == samples.maxlen:
        numerator = 0
        for i, item in enumerate(reversed(samples)):
            numerator += (1-alpha)**i * item
        ema = numerator / num_samples

        print("Max samples reached, calculated EMA is:", ema)

    samples.append(rms)

    print(len(samples), "samples recorded. Latest RMS:", rms)



with sd.InputStream(callback=audio_callback, channels=1, samplerate=44100, blocksize=int(44100 * duration)):
    print("Recording... Press Ctrl+C to stop.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Stopped recording.")
