import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
import pickle

DATASET_PATH = "../dataset/clacer_dataset.csv"
MODEL_PATH = "../compiler_error_model.pkl"

if not os.path.exists(DATASET_PATH):
    print("❌ Dataset file not found:", DATASET_PATH)
    exit()

df = pd.read_csv(DATASET_PATH)
# Some rows might be NA if error message was completely empty
df = df.dropna(subset=['error_message', 'label'])

X = df["error_message"]
y = df["label"]

# -------------------------------
# Convert text → TF-IDF features
# -------------------------------
vectorizer = TfidfVectorizer(ngram_range=(1, 2))
X_vec = vectorizer.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X_vec, y, test_size=0.2, random_state=42, stratify=y)

print("==== Week 9: Temporal Learning Simulation ====")
fractions = [0.2, 0.4, 0.6, 0.8, 1.0]

for frac in fractions:
    if frac < 1.0:
        # We slice the training set to simulate data growth
        X_sub, _, y_sub, _ = train_test_split(X_train, y_train, train_size=frac, random_state=42, stratify=y_train)
    else:
        X_sub, y_sub = X_train, y_train
        
    model_sim = LogisticRegression(max_iter=1000)
    model_sim.fit(X_sub, y_sub)
    acc = accuracy_score(y_test, model_sim.predict(X_test))
    print(f"Data size: {int(frac*100)}% -> Accuracy: {acc*100:.2f}%")

print("\n==== Final Advanced Model Training ====")
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

# Evaluate Baseline Confidence Calibration
print("\n[Baseline Confidence Distribution]")
probs = model.predict_proba(X_test)
max_probs = np.max(probs, axis=1)
ambiguous = sum(1 for p in max_probs if p < 0.65)
print(f"Total Test Samples: {len(y_test)}")
print(f"Samples flagged as 'Ambiguous' (Confidence < 65%): {ambiguous}")

predictions = model.predict(X_test)
print("\n📈 Classification Report:\n")
print(classification_report(y_test, predictions))

# Save the updated model
with open(MODEL_PATH, "wb") as f:
    pickle.dump((model, vectorizer), f)
    
print(f"✅ Advanced Logistic Regression model saved to {MODEL_PATH}")
