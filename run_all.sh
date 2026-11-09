#!/usr/bin/env bash
# Rebuilds the database and reproduces every number, table and figure in the README from scratch.
set -euo pipefail
cd "$(dirname "$0")"
python data/download.py
python -m src.etl
python -m src.kpis
python -m src.check_app
python -m src.report
jupyter nbconvert --to notebook --execute --inplace notebooks/01_analysis.ipynb --ExecutePreprocessor.timeout=600
echo "done: see README.md and results/; start the dashboard with: streamlit run app.py"
