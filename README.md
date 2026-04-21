# 🧠 Intelligent Compiler Suite

> ML-Enhanced Compiler Error Classification System with CWE Security Tagging, Time Complexity Analysis, and Developer Fingerprint Profiling.

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-black?logo=flask)](https://flask.palletsprojects.com/)
[![GCC](https://img.shields.io/badge/GCC-14-orange?logo=gnu)](https://gcc.gnu.org/)
[![ML](https://img.shields.io/badge/ML-Stacking%20Ensemble-purple)](https://scikit-learn.org/)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔴 **Error Detection** | Real GCC compilation with multi-error extraction |
| 🤖 **ML Classification** | Stacking Ensemble Classifier (Lexical / Syntax / Semantic) |
| 🛡️ **CWE Tagging** | Automatic CWE security ID assignment per error |
| ⏱️ **Time Complexity** | Static heuristic Big-O analysis of submitted code |
| 📍 **Row & Col Tracking** | Exact line and column number for every error |
| 🔦 **Editor Highlighting** | Error lines visually highlighted in the code editor |
| 👤 **Developer Profiling** | Session-level skill-level fingerprint |
| 📖 **Readability Scoring** | Rates how descriptive each compiler error message is |

---

## 🗂️ Project Structure

```
LJ/
├── webapp/
│   ├── app.py                   # Flask backend — ML pipeline, GCC, API
│   ├── templates/
│   │   └── index.html           # Single-page dashboard UI
│   └── static/
│       ├── style.css            # Dark glassmorphism design system
│       └── app.js               # Frontend logic (editor, results, highlights)
│
├── scripts/
│   ├── cwe_tagger.py            # CWE ID assignment module
│   ├── readability_scorer.py    # Error readability scorer (0–10)
│   ├── profiler.py              # Developer fingerprint profiler
│   ├── train_model.py           # Model training script
│   ├── train_stacking_model.py  # Stacking ensemble trainer
│   ├── compare_models.py        # Model comparison & benchmarking
│   ├── predict_from_file.py     # CLI: predict from a .c file
│   ├── predict_cli.py           # CLI: predict from stdin
│   ├── predict.py               # Core predict helper
│   ├── demo_pipeline.py         # Full end-to-end demo
│   ├── run_compiler.py          # GCC wrapper utility
│   ├── fetch_clacer.py          # CLACER dataset downloader
│   ├── clean_dataset.py         # Dataset cleaner
│   ├── fix_dataset.py           # Dataset fixer
│   ├── relabel_dataset.py       # Dataset relabeller
│   ├── check_distribution.py    # Dataset distribution checker
│   ├── batch_collect_errors.py  # Batch GCC error collector
│   └── confusion_matrix.py      # Confusion matrix generator
│
├── dataset/                     # Training data (CSV)
├── error_programs/              # Sample erroneous C programs
├── compiler_error_model.pkl     # Trained ML model (pickle)
└── mingw64/                     # Portable GCC toolchain (gitignored)
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- GCC (bundled via `mingw64/` or installed on PATH)

### 1 — Install Python dependencies

```bash
pip install flask scikit-learn numpy
```

### 2 — Train the model (first time only)

```bash
cd scripts
python train_stacking_model.py
```

### 3 — Launch the webapp

```bash
cd webapp
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

---

## 🎛️ How It Works

```
User submits C code
        │
        ▼
  GCC Compilation  ←── Custom Lexical Scanner (stray chars)
        │
        ▼
  Error Extraction + Deduplication
        │
        ▼
  ┌─────────────────────────────┐
  │ Layer 1: Deterministic Rules│  (100% accuracy on known patterns)
  │ Layer 2: ML Stacking Model  │  (fallback for unknown patterns)
  └─────────────────────────────┘
        │
        ▼
  CWE Tagger  ──►  Readability Scorer  ──►  Developer Profiler
        │
        ▼
  Time Complexity Analyser  (Big-O heuristic)
        │
        ▼
  JSON API response → Dashboard UI
```

---

## 📊 ML Model

- **Algorithm**: Stacking Ensemble (Logistic Regression + Random Forest + SVM meta-learner)
- **Dataset**: CLACER + custom augmented set (~10,000 labelled error messages)
- **Classes**: `LEXICAL` | `SYNTAX` | `SEMANTIC`
- **Accuracy**: 99.9% on rule-matched patterns, ~92% on novel ML patterns
- **Confidence threshold**: < 65% flagged as ambiguous

---

## 🔒 Security (CWE Coverage)

| Error Pattern | CWE ID | Severity |
|---|---|---|
| NULL / pointer dereference | CWE-476 | HIGH |
| Buffer overflow | CWE-120 | HIGH |
| Array out of bounds | CWE-119 | HIGH |
| Use after free | CWE-416 | CRITICAL |
| Double free | CWE-415 | CRITICAL |
| Format string | CWE-134 | MEDIUM |
| Lexical / malformed token | CWE-20 | MEDIUM |
| Syntax / grammar violation | CWE-1025 | LOW |
| General semantic flaw | CWE-699 | LOW |

---

## ⏱️ Time Complexity Detection

The analyser inspects the submitted code to estimate Big-O:

| Pattern Detected | Complexity |
|---|---|
| No loops, no recursion | O(1) — Constant |
| 1 loop | O(n) — Linear |
| 2 nested loops | O(n²) — Quadratic |
| 3 nested loops | O(n³) — Cubic |
| Logarithmic halving | O(log n) — Logarithmic |
| Recursive + divide | O(n log n) — Linearithmic |
| Unbounded recursion | O(2ⁿ) — Exponential |

---

## 👥 Team

PBL Group Project — Computer Science, LJ University  
Academic Year 2025–2026

---

*Built with ❤️ using Flask, scikit-learn, GCC, and vanilla JS.*
