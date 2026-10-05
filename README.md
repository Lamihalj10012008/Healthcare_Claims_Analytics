# Healthcare Claims Analytics

A full-stack medical billing analytics workspace for screening categorical claim attributes with the **Chi-Square Test of Independence**.

> Statistical association does not imply causation.

## Overview

Upload a synthetic or de-identified healthcare claims CSV, choose the outcome column and significance level, then inspect live statistical results. The backend performs preprocessing, categorical feature detection, contingency-table construction, SciPy Chi-Square tests, expected-frequency checks, feature export, HTML report generation, and an optional model comparison.

## Problem Statement

Medical billing teams process many categorical attributes but need a transparent way to identify which fields are associated with approval or denial outcomes. This project turns that question into a repeatable statistical workflow.

## Features

- CSV upload with file validation and a 15 MB limit
- Missing categorical-value handling and duplicate removal
- Automatic categorical/numerical detection with identifier exclusion
- Selectable target column and alpha values 0.01, 0.05, and 0.10
- Chi-Square statistic, p-value, degrees of freedom, observed and expected frequencies
- Warnings for small expected cell frequencies
- Dashboard, outcome insights, feature detail modal, sortable-ready results table, and responsive layout
- Selected-feature CSV export and downloadable HTML statistical report
- Optional Logistic Regression and Random Forest comparison using all vs screened features
- SQLite metadata for datasets, runs, and result rows
- FastAPI documentation at `/docs`

## System Architecture

`CSV upload -> FastAPI validation -> Pandas preprocessing -> SciPy chi2_contingency -> API JSON -> React dashboard`

Uploaded files and generated reports are excluded from Git. SQLite stores metadata and analysis results, not patient information.

## Technology Stack

- Frontend: React, Vite, Axios, Lucide icons, CSS
- Backend: Python, FastAPI, Pandas, NumPy, SciPy, scikit-learn
- Storage: SQLite and local runtime folders

## Dataset

`backend/data/sample_claims.csv` is generated locally with 600 synthetic claims. No real patient information is used. Regenerate it with:

```powershell
cd backend
python data/generate_sample.py
```

## Chi-Square Methodology

For every valid categorical feature, the service creates a contingency table against the selected target and calls `scipy.stats.chi2_contingency`. A feature is marked significant when `p_value < significance_level`.

Expected frequencies are returned and cells below 5 trigger a limitation warning. Identifier-like and high-cardinality columns are excluded from screening. Missing categorical values become `Unknown`.

## Installation

### Backend Setup

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The API runs at `http://localhost:8000`; interactive docs are at `http://localhost:8000/docs`.

### Frontend Setup

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

The UI runs at `http://localhost:5173`. Copy `.env.example` to `.env` only when the API is hosted somewhere other than the default `http://localhost:8000/api`.

## Example Workflow

1. Open the frontend.
2. Go to Dataset Upload and choose `backend/data/sample_claims.csv`.
3. Keep `Claim_Status` as the target and choose `0.05`.
4. Run the analysis.
5. Open Feature Analysis rows for observed and expected frequencies.
6. Review Claim Insights, optionally run ML Analysis, then download a CSV or HTML report.

## Results and Interpretation

Results are computed from the uploaded file at request time. A significant result means the data provides evidence of association at the selected alpha; it does not mean the feature causes approval or denial, and it does not guarantee better ML performance.

## Limitations

Chi-Square approximations can be unreliable with sparse expected counts. Results are observational, sensitive to preprocessing and category quality, and do not provide medical advice. ML comparisons use a single stratified holdout split for demonstration.

## Future Enhancements

Denial prediction, cost analysis, fraud/anomaly detection, insurer comparison, processing-time analysis, explainable AI, role-based access, PostgreSQL, and cloud deployment.

## TPIC Alignment

The project demonstrates data preprocessing and statistical analysis (CO2), feature relationship evaluation and visualization (CO4), and statistical feature screening in healthcare billing (CO5), aligned with “Feature Independence Analysis in Data Science Using Chi-Square Test.”

## Privacy and Ethics

Use synthetic or de-identified datasets only. Do not upload names, addresses, phone numbers, member IDs, medical record numbers, or other personally identifiable information.

## Author

Student project / TPIC micro-project demonstration.
