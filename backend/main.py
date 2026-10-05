from __future__ import annotations
import json, re, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
try:
    from .database import get_connection, init_db
    from .services.preprocessing import PreparedDataset, analysis_features, prepare_dataset
    from .services.chi_square import feature_detail, run_feature_test
    from .services.ml_model import evaluate
    from .services.report_generator import write_html_report
except ImportError:
    from database import get_connection, init_db
    from services.preprocessing import PreparedDataset, analysis_features, prepare_dataset
    from services.chi_square import feature_detail, run_feature_test
    from services.ml_model import evaluate
    from services.report_generator import write_html_report

ROOT = Path(__file__).parent
UPLOAD_DIR = ROOT / "uploads"
REPORT_DIR = ROOT / "reports" / "generated"
UPLOAD_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)
DATASETS: dict[str, PreparedDataset] = {}
ANALYSES: dict[str, dict[str, Any]] = {}

app = FastAPI(title="Healthcare Claims Analytics API", version="1.0.0", description="Real-time categorical feature screening using the Chi-Square Test of Independence.")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
init_db()

class AnalyzeRequest(BaseModel):
    dataset_id: str
    target_column: str
    significance_level: float = Field(0.05, ge=0.01, le=0.10)

class ExportRequest(BaseModel):
    dataset_id: str
    target_column: str
    features: list[str]

class MLRequest(BaseModel):
    dataset_id: str
    target_column: str
    selected_features: list[str] = []


def safe_name(filename: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", Path(filename).name)


def dataset_payload(dataset_id: str, filename: str, prepared: PreparedDataset) -> dict:
    return {"dataset_id": dataset_id, "filename": filename, "rows": len(prepared.frame), "columns": len(prepared.frame.columns), "column_names": prepared.frame.columns.tolist(), "categorical_columns": prepared.categorical_columns, "numerical_columns": prepared.numerical_columns, "missing_values": prepared.missing_summary, "duplicate_rows_removed": prepared.duplicate_rows_removed}


def get_dataset(dataset_id: str) -> PreparedDataset:
    if dataset_id not in DATASETS:
        raise HTTPException(404, "Dataset was not found or has expired.")
    return DATASETS[dataset_id]


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/upload")
async def upload_dataset(file: UploadFile = File(...)) -> dict:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Please upload a CSV file.")
    content = await file.read()
    if len(content) > 15 * 1024 * 1024:
        raise HTTPException(413, "The uploaded file is larger than the 15 MB limit.")
    try:
        frame = pd.read_csv(pd.io.common.BytesIO(content))
        prepared = prepare_dataset(frame)
    except Exception as error:
        raise HTTPException(400, "Unable to read the uploaded file.") from error
    dataset_id = str(uuid.uuid4())
    DATASETS[dataset_id] = prepared
    (UPLOAD_DIR / f"{dataset_id}_{safe_name(file.filename)}").write_bytes(content)
    metadata = dataset_payload(dataset_id, safe_name(file.filename), prepared)
    with get_connection() as connection:
        connection.execute("INSERT INTO datasets VALUES (?, ?, ?, ?, ?, ?, ?)", (dataset_id, metadata["filename"], datetime.now(timezone.utc).isoformat(), metadata["rows"], metadata["columns"], None, json.dumps(metadata)))
    return metadata


@app.get("/api/dataset/{dataset_id}")
def dataset_metadata(dataset_id: str) -> dict:
    prepared = get_dataset(dataset_id)
    with get_connection() as connection:
        row = connection.execute("SELECT metadata_json FROM datasets WHERE id = ?", (dataset_id,)).fetchone()
    return json.loads(row["metadata_json"]) if row else dataset_payload(dataset_id, "uploaded.csv", prepared)


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest) -> dict:
    prepared = get_dataset(request.dataset_id)
    if request.target_column not in prepared.frame.columns:
        raise HTTPException(400, "Please select a target column.")
    if prepared.frame[request.target_column].nunique(dropna=False) < 2:
        raise HTTPException(400, "The selected target requires at least two categories for Chi-Square analysis.")
    features = analysis_features(prepared, request.target_column)
    results = []
    for feature in features:
        try:
            results.append(run_feature_test(prepared.frame, feature, request.target_column, request.significance_level))
        except ValueError:
            continue
    result = {"dataset_id": request.dataset_id, "target_column": request.target_column, "significance_level": request.significance_level, "total_features": len(results), "significant_features": sum(item["significant"] for item in results), "non_significant_features": sum(not item["significant"] for item in results), "results": results}
    analysis_id = str(uuid.uuid4())
    result["analysis_id"] = analysis_id
    ANALYSES[request.dataset_id] = result
    with get_connection() as connection:
        connection.execute("UPDATE datasets SET target_column = ? WHERE id = ?", (request.target_column, request.dataset_id))
        connection.execute("INSERT INTO analysis_runs VALUES (?, ?, ?, ?)", (analysis_id, request.dataset_id, request.significance_level, datetime.now(timezone.utc).isoformat()))
        connection.executemany("INSERT INTO analysis_results (analysis_run_id, feature_name, chi_square, p_value, degrees_of_freedom, significant) VALUES (?, ?, ?, ?, ?, ?)", [(analysis_id, item["feature"], item["chi_square"], item["p_value"], item["degrees_of_freedom"], item["significant"]) for item in results])
    return result


@app.get("/api/feature/{dataset_id}/{feature}")
def feature(dataset_id: str, feature: str) -> dict:
    prepared = get_dataset(dataset_id)
    analysis = ANALYSES.get(dataset_id)
    if not analysis:
        raise HTTPException(400, "Run an analysis before opening feature details.")
    if feature not in prepared.frame.columns:
        raise HTTPException(404, "Feature was not found.")
    return feature_detail(prepared.frame, feature, analysis["target_column"], analysis["significance_level"])


@app.get("/api/summary/{dataset_id}")
def summary(dataset_id: str) -> dict:
    prepared = get_dataset(dataset_id)
    analysis = ANALYSES.get(dataset_id, {"significant_features": 0})
    target = analysis.get("target_column")
    counts = prepared.frame[target].value_counts() if target else pd.Series(dtype=int)
    approved = int(next((value for key, value in counts.items() if str(key).lower() in {"approved", "approve", "yes"}), 0))
    denied = int(next((value for key, value in counts.items() if str(key).lower() in {"denied", "deny", "no"}), 0))
    return {"total_claims": len(prepared.frame), "approved_claims": approved, "denied_claims": denied, "approval_percentage": round(approved / len(prepared.frame) * 100, 2) if len(prepared.frame) else 0, "denial_percentage": round(denied / len(prepared.frame) * 100, 2) if len(prepared.frame) else 0, "categorical_features": len(prepared.categorical_columns), "significant_features": analysis.get("significant_features", 0), "target_distribution": {str(key): int(value) for key, value in counts.items()}}


@app.post("/api/export")
def export_features(request: ExportRequest) -> FileResponse:
    prepared = get_dataset(request.dataset_id)
    valid = [feature for feature in request.features if feature in prepared.frame.columns]
    if request.target_column not in prepared.frame.columns or not valid:
        raise HTTPException(400, "Select a valid target and at least one feature.")
    path = REPORT_DIR / f"selected_claim_features_{request.dataset_id}.csv"
    prepared.frame[valid + [request.target_column]].to_csv(path, index=False)
    return FileResponse(path, filename="selected_claim_features.csv", media_type="text/csv")


@app.post("/api/ml-analysis")
def ml_analysis(request: MLRequest) -> dict:
    prepared = get_dataset(request.dataset_id)
    all_features = [column for column in prepared.frame.columns if column != request.target_column and column.lower() not in {"claim_id", "id"}]
    selected = request.selected_features or all_features
    try:
        return {"all_features": evaluate(prepared.frame, request.target_column, all_features), "selected_features": evaluate(prepared.frame, request.target_column, [feature for feature in selected if feature in all_features])}
    except Exception as error:
        raise HTTPException(400, str(error)) from error


@app.post("/api/generate-report")
def generate_report(request: AnalyzeRequest) -> FileResponse:
    prepared = get_dataset(request.dataset_id)
    analysis = ANALYSES.get(request.dataset_id)
    if not analysis:
        analysis = analyze(request)
    dataset = dataset_metadata(request.dataset_id)
    summary_data = summary(request.dataset_id)
    path = REPORT_DIR / f"statistical_report_{request.dataset_id}.html"
    write_html_report(path, dataset, analysis, summary_data)
    return FileResponse(path, filename="healthcare_claims_statistical_report.html", media_type="text/html")
