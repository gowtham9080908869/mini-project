import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# 1. Load the data
print("Checking for training data...")
try:
    df = pd.read_csv('training_data.csv')
    print("Found training_data.csv! Starting training...")
except:
    print("Error: Could not find 'training_data.csv'. Make sure you ran Phase 2 first!")
    exit()

# 2. Prepare the AI inputs
X = df[['velocity', 'acceleration']]
y = df['label']

# 3. Split and Train
print("Splitting data and building the model...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# 4. Show results (EMOJIS REMOVED TO PREVENT CRASH)
predictions = model.predict(X_test)
acc = accuracy_score(y_test, predictions) * 100
print("---------------------------------------")
print(f"TRAINING COMPLETE! Accuracy: {acc:.2f}%")
print("---------------------------------------")

# 5. Save the 'Brain'
joblib.dump(model, 'captcha_guard.pkl')
print("Model saved successfully as 'captcha_guard.pkl'")