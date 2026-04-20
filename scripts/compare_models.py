import os
import pandas as pd
import numpy as np
import pickle
import time
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, f1_score, classification_report

# Paths
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(_SCRIPT_DIR, "..", "dataset", "clacer_dataset.csv")
MODEL_PATH = os.path.join(_SCRIPT_DIR, "..", "compiler_error_model.pkl")

def train_and_evaluate(name, model, X_train, X_test, y_train, y_test):
    print(f"\n--- Training {name} ---")
    start_time = time.time()
    model.fit(X_train, y_train)
    train_time = time.time() - start_time
    
    predictions = model.predict(X_test)
    acc = accuracy_score(y_test, predictions)
    f1 = f1_score(y_test, predictions, average='weighted')
    
    print(f"Done in {train_time:.2f}s | Accuracy: {acc*100:.2f}% | F1-Score: {f1*100:.2f}%")
    return {
        "name": name,
        "model": model,
        "accuracy": acc,
        "f1_score": f1,
        "report": classification_report(y_test, predictions)
    }

def main():
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Dataset not found at {DATASET_PATH}")
        return

    print("Loading Expanded Dataset (9,989 samples)...")
    df = pd.read_csv(DATASET_PATH).dropna(subset=['error_message', 'label'])
    
    X = df["error_message"]
    y = df["label"]

    print("Vectorizing Text Data (TF-IDF)...")
    vectorizer = TfidfVectorizer(ngram_range=(1, 2))
    X_vec = vectorizer.fit_transform(X)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X_vec, y, test_size=0.2, random_state=42, stratify=y
    )

    models_to_test = [
        ("Logistic Regression", LogisticRegression(max_iter=1000)),
        ("Linear SVM", SVC(kernel='linear', probability=True)),
        ("Multinomial Naive Bayes", MultinomialNB())
    ]

    results = []
    for name, model in models_to_test:
        res = train_and_evaluate(name, model, X_train, X_test, y_train, y_test)
        results.append(res)

    # Find the winner based on F1-Score (best balance for imbalanced classes)
    winner = max(results, key=lambda x: x['f1_score'])

    print("\n" + "="*40)
    print("      COMPETITION LEADERBOARD")
    print("="*40)
    for res in results:
        status = " (WINNER)" if res == winner else "         "
        print(f"{status} {res['name']:<20} | F1: {res['f1_score']*100:.2f}% | Acc: {res['accuracy']*100:.2f}%")
    print("="*40)

    print(f"\nSelecting {winner['name']} as the production model.")
    print("\nFinal Classification Report:\n")
    print(winner['report'])

    # Save the winner
    with open(MODEL_PATH, "wb") as f:
        # We always save as tuple of (model, vectorizer) to keep compatibility with app.py
        pickle.dump((winner['model'], vectorizer), f)
    
    print(f"\nBest model ({winner['name']}) saved successfully to {os.path.basename(MODEL_PATH)}")

if __name__ == "__main__":
    main()
