from __future__ import annotations
import pandas as pd
from scipy.stats import chi2_contingency


def run_feature_test(frame: pd.DataFrame, feature: str, target: str, significance_level: float) -> dict:
    table = pd.crosstab(frame[feature], frame[target])
    if table.shape[0] < 2 or table.shape[1] < 2:
        raise ValueError(f"{feature} was skipped because it has fewer than two categories.")
    chi_square, p_value, degrees_of_freedom, expected = chi2_contingency(table.to_numpy())
    expected_df = pd.DataFrame(expected, index=table.index, columns=table.columns)
    small_cells = int((expected_df < 5).sum().sum())
    warning = None
    if small_cells:
        warning = "Chi-Square approximation may be unreliable because some expected cell frequencies are small. Consider combining sparse categories or using an appropriate alternative test."
    significant = bool(p_value < significance_level)
    return {
        "feature": feature, "chi_square": float(chi_square), "p_value": float(p_value),
        "degrees_of_freedom": int(degrees_of_freedom), "significant": significant,
        "interpretation": "The analysis provides evidence of an association between this feature and claim outcome at the selected significance level." if significant else "The analysis does not provide sufficient evidence of an association between this feature and claim outcome at the selected significance level.",
        "warning": warning,
    }


def feature_detail(frame: pd.DataFrame, feature: str, target: str, significance_level: float) -> dict:
    result = run_feature_test(frame, feature, target, significance_level)
    observed = pd.crosstab(frame[feature], frame[target])
    _, _, _, expected = chi2_contingency(observed.to_numpy())
    result.update({"feature": feature, "target_column": target,
        "categories": [str(value) for value in observed.index],
        "target_categories": [str(value) for value in observed.columns],
        "observed": [[int(value) for value in row] for row in observed.to_numpy()],
        "expected": [[round(float(value), 3) for value in row] for row in expected],
    })
    return result
