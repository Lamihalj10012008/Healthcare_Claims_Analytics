from __future__ import annotations
from dataclasses import dataclass
import pandas as pd

ID_NAMES = {"claim_id", "id", "member_id", "patient_id", "record_id"}

@dataclass
class PreparedDataset:
    frame: pd.DataFrame
    categorical_columns: list[str]
    numerical_columns: list[str]
    missing_summary: dict[str, int]
    duplicate_rows_removed: int


def prepare_dataset(frame: pd.DataFrame) -> PreparedDataset:
    if frame.empty or len(frame.columns) == 0:
        raise ValueError("The uploaded dataset contains no records.")
    frame = frame.copy()
    frame.columns = [str(column).strip() for column in frame.columns]
    original_row_count = len(frame)
    frame = frame.drop_duplicates()
    duplicate_rows_removed = original_row_count - len(frame)
    missing_summary = {str(column): int(value) for column, value in frame.isna().sum().items() if value}
    categorical_columns = frame.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
    numerical_columns = frame.select_dtypes(include="number").columns.tolist()
    for column in categorical_columns:
        frame[column] = frame[column].astype("string").fillna("Unknown").str.strip()
    return PreparedDataset(frame, categorical_columns, numerical_columns, missing_summary, duplicate_rows_removed)


def analysis_features(prepared: PreparedDataset, target_column: str) -> list[str]:
    features = []
    for column in prepared.categorical_columns:
        if column == target_column or column.lower() in ID_NAMES:
            continue
        unique_count = prepared.frame[column].nunique(dropna=False)
        if 2 <= unique_count <= 50:
            features.append(column)
    return features
