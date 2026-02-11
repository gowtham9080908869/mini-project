import pandas as pd
import numpy as np
import time

data = []
# Simulate a bot moving from (0,0) to (500,500) in a perfectly straight line
start_pos = (0, 0)
end_pos = (500, 500)
steps = 100

x_path = np.linspace(start_pos[0], end_pos[0], steps)
y_path = np.linspace(start_pos[1], end_pos[1], steps)

for i in range(steps):
    data.append({
        'x': x_path[i], 
        'y': y_path[i], 
        'time': time.time() + (i * 0.01), # Perfectly consistent speed
        'label': 'bot'
    })

df = pd.DataFrame(data)
df.to_csv('bot_data.csv', index=False)
print("Bot simulation complete. Saved to bot_data.csv")