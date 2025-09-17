
import sounddevice as sd
import win32com.client
import numpy as np
import datetime
import tkinter
import json


###############################
### Load Settings From JSON ###
###############################

with open('settings.json', 'r') as f:
    settings = json.load(f)

    # Smoothing factor for expoential moving average
    alpha = settings["exponential_moving_average_alpha"]

    # How many seconds of audio in each sample
    duration = settings["sample_duration"]

    # To trigger loud noise detection, RMS > EMA * threshold
    threshold = settings["threshold"]

    # Minimum RMS value to trigger a loud noise detection
    min_trigger_rms = settings["min_trigger_rms"]

    # Minimum time between notifications
    interval_seconds = settings["min_notification_interval_seconds"]
    min_notification_interval = datetime.timedelta(seconds=interval_seconds)

    # Determine tts message
    tts_message = settings["tts_message"]

    # Number of loud noises needed to trigger burst alert
    burst_alert_count = settings["burst_alert_count"]

    # Number of seconds that a message is kept in mind when considering burst alert
    burst_alert_window = settings["burst_alert_window"]

    # Message to use for burst alert
    burst_alert_message = settings["burst_alert_message"]


#######################################
### Define Helper Functions/Classes ###
#######################################

# Low-latency non-blocking TTS using SAPI - unfortunately Windows only
class FastTTS:
    def __init__(self):
        self.speaker = win32com.client.Dispatch("SAPI.SpVoice")
    def say(self, text: str):
        self.speaker.Speak(text, 1)


# Callback function to process audio data
def audio_callback(indata, frames, time, status):
    global ema, cycles_to_warm, first_cycle, engine, last_notification, alert_history

    # Print any errors if they show up
    if status:
        print(status)

    # Use Root of Mean Square to create a single value for volume that emphasizes louder sounds
    rms = np.sqrt(np.mean(indata**2))

    # Calculate exponetial moving average
    ema = (ema * (1 - alpha)) + (rms * alpha)

    # Once ema warms up use it
    if cycles_to_warm == 0:
        print(f"RMS: {rms:.4f}, EMA: {ema:.4f}")

        # Detect loud noise using threshold
        if rms > (ema * threshold) and (rms > min_trigger_rms):
            print("Loud noise detected!")

            # Check if enough time has passed since the last notification
            current_time = datetime.datetime.now()
            if last_notification is None or (current_time - last_notification) > min_notification_interval:
                last_notification = current_time

                # Add current time to alert history
                alert_history.append(current_time)

                # Remove old alerts from history
                alert_history = [t for t in alert_history if (current_time - t).total_seconds() <= burst_alert_window]

                # Determine message to send based on number of alerts in history
                message = tts_message if len(alert_history) < burst_alert_count else burst_alert_message

                # Send Mesage
                print("Notifying user...")
                tts.say(message)

            else:
                print("Notification throttled.")

    # For the first cycle set ema to rms to 
    elif first_cycle:
        ema = rms
        first_cycle = False
        print(f"RMS: {rms:.4f}, Intializing EMA")

    # Don't print ema for a bit to avoid starting spikes
    else:
        cycles_to_warm -= 1
        print(f"RMS: {rms:.4f}, warming up EMA")


############################
### Initialize Variables ###
############################

# Instiantiate ema variable
ema = 0.0

# Initialize last notification time
last_notification = None

# Set flat for first ema cycle
first_cycle = True

# Determine how many cycles are needed to warm up the ema
cycles_to_warm = int(1/alpha)

# Initialize alert history for burst detection
alert_history = []

# Initialze tts engine
tts = FastTTS()


#################################
### Initialize Tkinter Window ###
#################################

window = tkinter.Tk()
window.title("Loud Noise Monitor")
window.geometry("400x400")


##########################
### Start Audio Stream ###
##########################

# Define/start audio stream
stream = sd.InputStream(callback=audio_callback, channels=1, samplerate=44100, blocksize=int(44100 * duration))
stream.start()

# Start tkinter application
window.mainloop()

# Stop/close audio stream when tkinter window is closed
stream.stop()
stream.close()
