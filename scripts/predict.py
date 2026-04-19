import pickle

# Load saved model
with open("../compiler_error_model.pkl", "rb") as f:
    model, vectorizer = pickle.load(f)

print("Compiler Error Classifier (type 'exit' to stop)")

while True:
    error_msg = input("\nPaste compiler error: ")

    if error_msg.lower() == "exit":
        break

    vec = vectorizer.transform([error_msg])
    prediction = model.predict(vec)[0]

    print("Predicted error type:", prediction)
