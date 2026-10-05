from __future__ import annotations
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


def evaluate(frame: pd.DataFrame, target: str, features: list[str]) -> dict:
    data = frame[features + [target]].dropna()
    if data[target].nunique() < 2 or len(data) < 20:
        raise ValueError("ML analysis requires at least 20 rows and two target categories.")
    x_train, x_test, y_train, y_test = train_test_split(data[features], data[target], test_size=0.25, random_state=42, stratify=data[target])
    categorical = [column for column in features if str(data[column].dtype) in ("object", "string", "category")]
    numeric = [column for column in features if column not in categorical]
    transformer = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), categorical), ("num", "passthrough", numeric)])
    models = {"Logistic Regression": LogisticRegression(max_iter=1000), "Random Forest": RandomForestClassifier(n_estimators=120, random_state=42, class_weight="balanced")}
    output = []
    for name, model in models.items():
        pipeline = Pipeline([("transform", transformer), ("model", model)])
        pipeline.fit(x_train, y_train)
        predicted = pipeline.predict(x_test)
        output.append({"model": name, "accuracy": round(float(accuracy_score(y_test, predicted)), 4), "precision": round(float(precision_score(y_test, predicted, average="weighted", zero_division=0)), 4), "recall": round(float(recall_score(y_test, predicted, average="weighted", zero_division=0)), 4), "f1_score": round(float(f1_score(y_test, predicted, average="weighted", zero_division=0)), 4), "confusion_matrix": confusion_matrix(y_test, predicted).tolist()})
    return output
