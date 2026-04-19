import pickle

# -------------------------------
# Load trained model and vectorizer
# -------------------------------
with open("../compiler_error_model.pkl", "rb") as f:
    model, vectorizer = pickle.load(f)

print("=" * 60)
print("      COMPILER ERROR CLASSIFICATION SYSTEM")
print("=" * 60)
print("Enter a compiler error message below.")
print("Type 'exit' to quit.\n")

while True:
    error_msg = input(">> ").strip()

    if error_msg.lower() == "exit":
        print("\nExiting system. Goodbye!")
        break

    if not error_msg:
        print("Please enter a valid error message.")
        continue

    error_msg = error_msg.lower()

    vec = vectorizer.transform([error_msg])
    prediction = model.predict(vec)[0]

    print(f"\nPredicted Error Type: {prediction.upper()}")

    # Confidence (if supported)
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(vec)[0]
        confidence = max(probabilities) * 100
        print(f"Confidence: {confidence:.2f}%")
    else:
        print("Confidence: Not available for this model.")

    print("-" * 60)