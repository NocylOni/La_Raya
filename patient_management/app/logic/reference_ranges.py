"""Common lab reference ranges, used to auto-flag abnormal results and to
pre-fill reference_low/high when a clinician doesn't enter them manually.

Not exhaustive / not a substitute for lab-provided reference ranges — meant
as a sensible default for common tests.
"""
from __future__ import annotations

# name -> (low, high, unit)
REFERENCE_RANGES: dict[str, tuple[float, float, str]] = {
    "glucose": (70, 99, "mg/dL"),
    "hba1c": (4.0, 5.6, "%"),
    "hemoglobin": (12.0, 17.5, "g/dL"),
    "hematocrit": (36.0, 50.0, "%"),
    "wbc": (4.5, 11.0, "x10^9/L"),
    "platelets": (150, 450, "x10^9/L"),
    "sodium": (135, 145, "mmol/L"),
    "potassium": (3.5, 5.1, "mmol/L"),
    "chloride": (96, 106, "mmol/L"),
    "creatinine": (0.6, 1.3, "mg/dL"),
    "bun": (7, 20, "mg/dL"),
    "total cholesterol": (0, 200, "mg/dL"),
    "ldl": (0, 100, "mg/dL"),
    "hdl": (40, 100, "mg/dL"),
    "triglycerides": (0, 150, "mg/dL"),
    "tsh": (0.4, 4.0, "mIU/L"),
    "alt": (7, 56, "U/L"),
    "ast": (10, 40, "U/L"),
    "calcium": (8.5, 10.2, "mg/dL"),
    "vitamin d": (30, 100, "ng/mL"),
}

VITAL_RANGES: dict[str, tuple[float, float]] = {
    "heart_rate": (60, 100),
    "resp_rate": (12, 20),
    "bp_systolic": (90, 120),
    "bp_diastolic": (60, 80),
    "spo2": (95, 100),
    "temp_c": (36.1, 37.2),
}


def lookup_reference_range(test_name: str) -> tuple[float, float, str] | None:
    return REFERENCE_RANGES.get(test_name.strip().lower())


def flag_vital(vital_name: str, value: float | None) -> str:
    if value is None:
        return "unknown"
    range_ = VITAL_RANGES.get(vital_name)
    if range_ is None:
        return "unknown"
    low, high = range_
    if value < low:
        return "low"
    if value > high:
        return "high"
    return "normal"
