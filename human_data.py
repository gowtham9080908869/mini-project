import pandas as pd
from pynput import mouse
import time

data = []
print("Move your mouse around like you're solving a CAPTCHA. Press 'Esc' (manual stop) or wait 30 seconds.")

def on_move(x, y):
    # Record the x, y position and the current time
    data.append({'x': x, 'y': y, 'time': time.time(), 'label': 'human'})

# Start listening for 5 seconds
with mouse.Listener(on_move=on_move) as listener:
    time.sleep(30) 
    listener.stop()

# Save to a CSV file
df = pd.DataFrame(data)
df.to_csv('human_data.csv', index=False)
print(f"Captured {len(df)} data points. Saved to human_data.csv")