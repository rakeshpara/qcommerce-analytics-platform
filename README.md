# Quick Commerce Analytics Platform

Analytics workspace for sales and inventory performance, built for exploratory analysis, feature engineering, and dashboarding.

## Raw data
- `data/raw/Adventures-Online-Sales.xlsx`
- `data/raw/Online Retail.xlsx`

## Project structure
- `data/raw/`: source files (immutable)
- `data/interim/`: cleaned intermediate datasets
- `data/processed/`: model/dashboard-ready datasets
- `notebooks/`: exploratory notebooks
- `src/qcommerce_analytics/`: reusable Python package
- `configs/`: YAML/JSON config files
- `scripts/`: one-off and scheduled scripts
- `tests/`: unit/integration tests
- `app/`: dashboard app code
- `reports/figures/`: generated visuals
- `logs/`: runtime logs

## Setup
1. Create venv (already created by this setup):
   - Windows PowerShell: `python -m venv .venv`
2. Activate environment:
   - `./.venv/Scripts/Activate.ps1`
3. Install dependencies:
   - `python -m pip install --upgrade pip`
   - `pip install -r requirements.txt`
   - `pip install -r requirements-dev.txt`

## Run dashboard
- `streamlit run app/main.py`
