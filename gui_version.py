
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
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

    # Length of history to keep for graphing
    graph_history = settings["graph_history_length"]

    # Max number of events allowed in event log
    event_log_limit = settings["event_log_limit"]

    # Graph Y axis limit
    ylimit = settings["graph_ylimit"]

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
    global ema, cycles_to_warm, first_cycle, engine, last_notification, alert_history, rms_history, ema_history

    # Print any errors if they show up
    if status:
        print(status)

    # Use Root of Mean Square to create a single value for volume that emphasizes louder sounds
    rms = np.sqrt(np.mean(indata**2))

    # Add most recent rms and only keep up to graph_history number of values
    rms_history.append(rms)
    rms_history = rms_history[-graph_history:]

    # Calculate exponetial moving average
    ema = (ema * (1 - alpha)) + (rms * alpha)

    # Add most recent ema and only keep up to graph_history number of values
    ema_history.append(ema)
    ema_history = ema_history[-graph_history:]

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

                # Get data from event log
                event_log_data = event_log.get(1.0, tkinter.END).strip().split('\n')

                # Add new message to event log data
                event_log_data = [f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} - {message}"] + event_log_data

                # Keep only the most recent event_log_limit number of messages
                event_log_data = event_log_data[:event_log_limit]

                # Clear event log text box
                event_log.delete(1.0, tkinter.END)

                # Update event log text box
                event_log.insert(tkinter.END, '\n'.join(event_log_data))

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


# Function to update graph
def update_graph():
    global rms_history, ema_history, graph_update_handle

    if not(len(rms_history) == 0 or len(ema_history) == 0):
        x = np.arange(len(rms_history))
        rms_line.set_data(x, rms_history)
        ema_line.set_data(x, ema_history)

    canvas.draw()
    duration_ms = int(duration * 1000)
    graph_update_handle = window.after(duration_ms, update_graph)


# Function to ensure proper tkinter shutdown
def shutdown():
    global graph_update_handle, stream

    # Stop graph update loop
    if graph_update_handle is not None:
        window.after_cancel(graph_update_handle)

    # Stop/close audio stream
    stream.stop()
    stream.close()

    # Close tkinter window
    window.quit()
    window.destroy()


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

# Initialize ema history
ema_history = []

# Initialize rms history
rms_history = []

# Graph Upate Function Handle
graph_update_handle = None


#################################
### Initialize Tkinter Window ###
#################################

window = tkinter.Tk()
window.title("Loud Noise Monitor")
window.geometry("400x630")

# Bind cleaner shutdown
window.protocol("WM_DELETE_WINDOW", shutdown)


################################
### Initalize Matplot Figure ###
################################

# Initialize figure and empty plots
fix, ax = plt.subplots(figsize=(5, 4), dpi=100)
rms_line, = ax.plot([], [], "b-", label='RMS')
ema_line, = ax.plot([], [], "r-", label='EMA')

# Set Axis limits
ax.set_ylim(0, ylimit)
ax.set_xlim(0, graph_history)

# Set a vertical line on the min trigger rms
plt.axhline(y=min_trigger_rms, color="g", linestyle='-')

# Create canvas for tkinter and initally draw it
canvas = FigureCanvasTkAgg(fix, master=window)
canvas.draw()


######################
### Tkinter Layout ###
######################

# Raw Data Label
label = tkinter.Label(window, text="Underlying Audio Data")
label.config(font=("Arial", 12, 'bold'))
label.pack()

# Add Graph Data section
canvas.get_tk_widget().pack()

# Vertical Line
separator = tkinter.Frame(height=2, bd=1, relief=tkinter.SUNKEN)
separator.pack(fill=tkinter.X, padx=5, pady=5)

# Event Log Label
label = tkinter.Label(window, text="Loud Noise Message Event Log")
label.config(font=("Arial", 12, 'bold'))
label.pack()

# Loud Noise Event Text Box
event_log = tkinter.Text(window, height=10)
event_log.pack()


##########################
### Start Audio Stream ###
##########################

# Define/start audio stream
stream = sd.InputStream(callback=audio_callback, channels=1, samplerate=44100, blocksize=int(44100 * duration))
stream.start()

# Initialize graph update loop
update_graph()

# Start tkinter application
window.mainloop()
