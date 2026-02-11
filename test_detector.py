import pandas as pd
import numpy as np
import joblib
from pynput import mouse
import time

# 1. LOAD THE TRAINED BRAIN
print("--------------------------------------------------")
print("SYSTEM LOADING...")
try:
    model = joblib.load('captcha_guard.pkl')
    print("AI Model Loaded Successfully.")
except:
    print("Error: captcha_guard.pkl not found!")
    exit()

# 2. RECORD LIVE MOVEMENT
data = []
print("--------------------------------------------------")
print("SECURITY CHECK: Move your mouse for 5 SECONDS")
print("--------------------------------------------------")

def on_move(x, y):
    data.append({'x': x, 'y': y, 'time': time.time()})

listener = mouse.Listener(on_move=on_move)
listener.start()
time.sleep(10)
listener.stop()

# 3. ANALYZE DATA
if len(data) > 5:
    df = pd.DataFrame(data)
    # Calculate physics
    df['dx'] = df['x'].diff().fillna(0)
    df['dy'] = df['y'].diff().fillna(0)
    df['dt'] = df['time'].diff().fillna(0.01)
    df['velocity'] = np.sqrt(df['dx']**2 + df['dy']**2) / df['dt']
    df['acceleration'] = df['velocity'].diff().fillna(0)

    # 4. PREDICT
    X_input = df[['velocity', 'acceleration']]
    predictions = model.predict(X_input)
    
    # Count results
    bot_hits = np.sum(predictions == 'bot')
    total = len(predictions)
    bot_ratio = (bot_hits / total) * 100

    print(f"Analysis Complete. Bot Probability: {bot_ratio:.2f}%")
    print("--------------------------------------------------")
    if bot_ratio > 50:
        print("RESULT: ACCESS DENIED (BOT DETECTED)")
    else:
        print("RESULT: ACCESS GRANTED (HUMAN VERIFIED)")
    print("--------------------------------------------------")
else:
    print("No movement detected.")