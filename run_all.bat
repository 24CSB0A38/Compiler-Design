@echo off
echo =========================================================
echo    🚀 14-WEEK ENHANCED ML PROJECT AUTOMATED RUNNER 🚀
echo =========================================================
echo.
echo Installing baseline ML dependencies if missing...
python -m pip install pandas scikit-learn numpy
echo.

echo [Step 1] Initializing CLACER Dataset Extractor...
echo Note: This accesses your local GCC compiler to format the data.
python scripts/fetch_clacer.py
echo.

echo [Step 2] Training LogisticRegression Model with Temporal Sim...
python scripts/train_model.py
echo.

echo [Step 3] Firing end-to-end Demonstration Pipeline on Sample C File...
echo Sample Target: error_programs/semantic/sem1.c
python scripts/demo_pipeline.py ../error_programs/semantic/sem1.c
echo.

echo =========================================================
echo ✅ ALL MODULES GENERATED AND PROJECT SUCCESSFULLY COMPLETED!
echo =========================================================
pause
