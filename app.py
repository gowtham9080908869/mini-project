from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import joblib

app = Flask(__name__)

# Load your trained AI brain
model = joblib.load('captcha_guard.pkl')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/verify', methods=['POST'])
def verify():
    # Get mouse data sent from the browser
    coords = request.json['coords']
    if len(coords) < 10:
        return jsonify({'status': 'Too fast! Are you a bot?', 'color': 'red'})

    # Process data exactly like your training script
    df = pd.DataFrame(coords)
    df['dx'] = df['x'].diff().fillna(0)
    df['dy'] = df['y'].diff().fillna(0)
    df['dt'] = df['time'].diff().fillna(0.01)
    df['velocity'] = np.sqrt(df['dx']**2 + df['dy']**2) / df['dt']
    df['acceleration'] = df['velocity'].diff().fillna(0)

    # Predict
    features = df[['velocity', 'acceleration']]
    prediction = model.predict(features)
    
    # Calculate bot probability
    bot_ratio = (np.sum(prediction == 'bot') / len(prediction)) * 100

    if bot_ratio > 50:
        return jsonify({'status': '🚨 BOT DETECTED!', 'color': 'red'})
    else:
        return jsonify({'status': '✅ HUMAN VERIFIED', 'color': 'green'})

if __name__ == '__main__':
    app.run(debug=True)