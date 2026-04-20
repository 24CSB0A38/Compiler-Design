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
from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.metrics import accuracy_score, f1_score, classification_report

# Paths
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(_SCRIPT_DIR, "..", "dataset", "clacer_dataset.csv")
MODEL_PATH = os.path.join(_SCRIPT_DIR, "..", "compiler_error_model.pkl")

def main():
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Dataset not found at {DATASET_PATH}")
        return

    print("Loading Expanded Dataset (~10,000 samples)...")
    df = pd.read_csv(DATASET_PATH).dropna(subset=['error_message', 'label'])
    
    X = df["error_message"]
    y = df["label"]

    print(f"Total samples shape: {df.shape}")
    print("Vectorizing Text Data (TF-IDF)...")
    vectorizer = TfidfVectorizer(ngram_range=(1, 2))
    X_vec = vectorizer.fit_transform(X)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X_vec, y, test_size=0.2, random_state=42, stratify=y
    )

    print("\nBuilding the Advanced Ensemble Stacking Classifier...")
    print("Base Models: 1) Linear SVM, 2) Multinomial Naive Bayes, 3) Random Forest")
    print("Meta-Model: Logistic Regression")

    # Define the base models
    base_estimators = [
        ('svm', SVC(kernel='linear', probability=True)),
        ('nb', MultinomialNB()),
        ('rf', RandomForestClassifier(n_estimators=50, random_state=42))
    ]

    # Initialize the Stacking Classifier
    stacking_model = StackingClassifier(
        estimators=base_estimators,
        final_estimator=LogisticRegression(max_iter=1000),
        cv=5,
        n_jobs=-1 # Use all available CPU cores for parallel training
    )

    print("\nTraining the Stacking Model (This might take a moment depending on your CPU)...")
    start_time = time.time()
    stacking_model.fit(X_train, y_train)
    train_time = time.time() - start_time
    print(f"Training completed in {train_time:.2f} seconds!")

    # Evaluate Performance
    print("\nEvaluating Model on Test Data...")
    predictions = stacking_model.predict(X_test)
    acc = accuracy_score(y_test, predictions)
    f1 = f1_score(y_test, predictions, average='weighted')

    print("\n" + "="*50)
    print("      *** ENSEMBLE MODEL LEADERBOARD ***")
    print("="*50)
    print(f"Model Architecture : Stacking Ensemble (SVM+NB+RF -> LR)")
    print(f"Voting Mechanism   : Soft Probabilities Meta-Weighting")
    print(f"Final Accuracy     : {acc*100:.2f}%")
    print(f"Final F1-Score     : {f1*100:.2f}%")
    print("="*50)

    print("\nClassification Report:\n")
    print(classification_report(y_test, predictions))

    # Save the powerful ensemble model
    print("Saving the model...")
    with open(MODEL_PATH, "wb") as f:
        pickle.dump((stacking_model, vectorizer), f)
    
    print(f"\nAdvanced Stacking model saved successfully to {os.path.basename(MODEL_PATH)}")
    print("Your project is now officially running on an Ensemble Architecture!")

if __name__ == "__main__":
    main()
