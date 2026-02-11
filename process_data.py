import pandas as pd
import numpy as np

def calculate_features(df):
    # 1. Calculate the difference between the current row and the previous row
    # diff() calculates: (Current Value - Previous Value)
    df['dx'] = df['x'].diff() # Change in X
    df['dy'] = df['y'].diff() # Change in Y
    df['dt'] = df['time'].diff() # Change in Time

    # 2. Calculate Distance (Pythagorean theorem: a^2 + b^2 = c^2)
    # This tells us the total length of the jump between points
    df['distance'] = np.sqrt(df['dx']**2 + df['dy']**2)

    # 3. Calculate Velocity (Speed = Distance / Time)
    df['velocity'] = df['distance'] / df['dt']

    # 4. Calculate Acceleration (Change in Velocity / Time)
    df['acceleration'] = df['velocity'].diff() / df['dt']

    # 5. Clean up: The first row will be empty (NaN) because there's no previous row to compare to
    df = df.dropna()
    
    # We only care about the behavioral features now, not the raw x/y positions
    return df[['velocity', 'acceleration', 'label']]

# Load the raw files
human_raw = pd.read_csv('human_data.csv')
bot_raw = pd.read_csv('bot_data.csv')

# Process them
human_features = calculate_features(human_raw)
bot_features = calculate_features(bot_raw)

# Combine them into one "Training Set"
final_data = pd.concat([human_features, bot_features])

# Save the smart data
final_data.to_csv('training_data.csv', index=False)

print("Data processed! We converted raw positions into Speed and Acceleration.")
print(final_data.head())