# Machine Learning-Based Compiler Error Classification 🔬

**NIT Warangal | PBL Project | Roll No: 24CSB0A38 | LJ Vishnu Vardhan**

An intelligent compiler analysis system that classifies GCC compiler errors into Lexical, Syntax, and Semantic categories using a hybrid Rule-Based + Machine Learning pipeline.

---

## 🚀 Live Demo

```bash
cd webapp
python app.py
# Open http://127.0.0.1:5000 in your browser
```

---

## 🏆 System Architecture

The system uses a **2-Layer Hybrid Classifier** for maximum accuracy:

### Layer 1 — Deterministic Rule Engine (99.9% confidence)
Instantly classifies unambiguous errors using pattern matching:
- **Lexical**: `stray`, `missing terminating`, `invalid suffix`, `empty character constant`
- **Syntax**: `expected ';'`, `expected ')'`, `at end of input`, `expected identifier`
- **Semantic**: `undeclared`, `conflicting types`, `incompatible types`, `too many arguments`

### Layer 2 — Machine Learning Model (97.1% accuracy)
For edge cases not caught by rules, a **Linear SVM** trained on **9,989 real GCC errors** handles classification.

---

## 📊 Model Performance

| Model | Accuracy | F1-Score |
|---|---|---|
| **Linear SVM (Winner)** | **97.10%** | **97.10%** |
| Logistic Regression | 85.64% | 84.01% |
| Multinomial Naive Bayes | 86.44% | 85.00% |

---

## 📁 Project Structure

```
LJ/
├── webapp/                     # Flask Web Application
│   ├── app.py                  # Main app with hybrid classifier
│   ├── templates/index.html    # Dashboard UI
│   └── static/
│       ├── app.js              # Frontend logic (no-refresh analysis)
│       └── style.css           # Dark glassmorphism UI
│
├── scripts/                    # ML Pipeline
│   ├── fetch_clacer.py         # Parallel dataset expansion (9,989 samples)
│   ├── relabel_dataset.py      # Dataset label sanitization
│   ├── compare_models.py       # Multi-model competition & auto-selection
│   ├── train_model.py          # Model training with temporal simulation
│   ├── cwe_tagger.py           # CWE security vulnerability tagger
│   ├── readability_scorer.py   # Error readability scoring (0-10)
│   └── profiler.py             # Developer fingerprint profiler
│
├── dataset/
│   ├── clacer_dataset.csv      # 9,989 real GCC errors (sanitized)
│   └── CLACER_repo/            # Raw CLACER research dataset (16,925 programs)
│
├── compiler_error_model.pkl    # Trained Linear SVM + TF-IDF vectorizer
├── mingw64/                    # Portable GCC compiler (local)
└── gcc.zip                     # GCC installer (Git LFS)
```

---

## ⚙️ Setup Instructions

### Prerequisites
```bash
pip install flask scikit-learn pandas numpy
```

### 1. Expand the Dataset (optional, already done)
```bash
cd scripts
python fetch_clacer.py        # Compiles 10,000 CLACER programs with GCC
python relabel_dataset.py     # Sanitizes labels for accuracy
```

### 2. Train / Compare Models
```bash
python compare_models.py      # Runs LR vs SVM vs Naive Bayes; saves best
```

### 3. Start the Web Server
```bash
cd webapp
python app.py
```

---

## 🔍 Features

| Feature | Description |
|---|---|
| **Multi-Error Detection** | Detects all errors in a single file, not just the first |
| **CWE Tagging** | Maps errors to CWE security IDs (CWE-20, CWE-476, CWE-699, etc.) |
| **Readability Score** | Rates error message clarity from 0–10 |
| **Developer Profiler** | Assesses skill level (Beginner/Intermediate/Advanced) based on error patterns |
| **File Upload** | Upload `.c` files directly or paste code in the editor |
| **Confidence Score** | Shows ML prediction confidence for each error |

---

## 📌 Dataset

The **CLACER Dataset** (Compiler Language Analysis and Classification of Error Reports) is a research dataset of real GCC-compiled student programs. We processed the raw programs through our local GCC installation to extract **9,989 authentic error messages** and sanitized the labels using heuristic rules.

---

## 🛠 Tech Stack

- **Backend**: Python, Flask
- **ML**: scikit-learn (SVM, Logistic Regression, Naive Bayes), TF-IDF
- **Frontend**: HTML5, Vanilla CSS (glassmorphism), JavaScript (async fetch)
- **Compiler**: GCC via MinGW64 (portable)
- **Dataset**: CLACER (NIT-Warangal PBL processed version)
