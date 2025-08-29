
import sounddevice as sd
import numpy as np

# Smoothing factor for expoential moving average
alpha = 0.05

# Instantiate a variable to hold an expontential moving average
ema = 0.0

# Count how many cycles have passed
cycles_to_warm = int(1/alpha)

# Flag to indicate the first cycle
first_cycle = True

# How many seconds of audio in each sample
duration = 0.1

# Threshold for detecting a loud noise
threshold = 4


def audio_callback(indata, frames, time, status):
    global ema, cycles_to_warm, first_cycle

    # Print any errors if they show up
    if status:
        print(status)

    # print(indata) # Raw audio data

    # Use Root of Mean Square to create a single value for volume that emphasizes louder sounds
    rms = np.sqrt(np.mean(indata**2))

    # Calculate exponetial moving average
    ema = (ema * (1 - alpha)) + (rms * alpha)

    # Once ema warms up use it
    if cycles_to_warm == 0:
        print(f"RMS: {rms:.4f}, EMA: {ema:.4f}")

        # Detect loud noise using threshold
        if rms > (ema * threshold):
            print("Loud noise detected!")

    # For the first cycle set ema to rms to 
    elif first_cycle:
        ema = rms
        first_cycle = False
        print(f"RMS: {rms:.4f}, Intializing EMA")

    # Don't print ema for a bit to avoid starting spikes
    else:
        cycles_to_warm -= 1
        print(f"RMS: {rms:.4f}, warming up EMA")



with sd.InputStream(callback=audio_callback, channels=1, samplerate=44100, blocksize=int(44100 * duration)):
    print("Recording... Press Ctrl+C to stop.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Stopped recording.")
