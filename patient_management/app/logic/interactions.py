"""Small curated drug-drug interaction dataset used for clinical alerts.

This is illustrative, not a substitute for a licensed drug interaction
database — it exists to demonstrate/exercise the alerting feature end to
end. Matching is done on generic-name substrings, case-insensitive.
"""
from __future__ import annotations

# Each entry: (drug_a, drug_b, severity, description)
KNOWN_INTERACTIONS: list[tuple[str, str, str, str]] = [
    ("warfarin", "aspirin", "major", "Increased bleeding risk"),
    ("warfarin", "ibuprofen", "major", "Increased bleeding risk"),
    ("warfarin", "naproxen", "major", "Increased bleeding risk"),
    ("warfarin", "amiodarone", "major", "Increased anticoagulant effect"),
    ("lisinopril", "potassium", "moderate", "Risk of hyperkalemia"),
    ("lisinopril", "spironolactone", "moderate", "Risk of hyperkalemia"),
    ("sildenafil", "nitroglycerin", "major", "Severe hypotension risk"),
    ("sildenafil", "isosorbide", "major", "Severe hypotension risk"),
    ("metformin", "contrast", "moderate", "Risk of lactic acidosis / renal impairment"),
    ("sertraline", "tramadol", "major", "Risk of serotonin syndrome"),
    ("fluoxetine", "tramadol", "major", "Risk of serotonin syndrome"),
    ("sertraline", "ibuprofen", "moderate", "Increased GI bleeding risk"),
    ("simvastatin", "clarithromycin", "major", "Increased risk of myopathy/rhabdomyolysis"),
    ("digoxin", "amiodarone", "major", "Increased digoxin levels/toxicity"),
    ("methotrexate", "trimethoprim", "major", "Increased methotrexate toxicity"),
    ("clopidogrel", "omeprazole", "moderate", "Reduced antiplatelet effect"),
]


def _matches(name: str, term: str) -> bool:
    return term.lower() in name.lower()


def check_drug_interactions(new_medication: str, active_medications: list[str]) -> list[dict]:
    """Return a list of {drug_a, drug_b, severity, description} for every
    known interaction between new_medication and the patient's active meds."""
    alerts = []
    for existing in active_medications:
        if _matches(existing, new_medication.split()[0]) or _matches(new_medication, existing.split()[0]):
            continue  # same drug, skip self-match noise
        for a, b, severity, description in KNOWN_INTERACTIONS:
            pair_hits = (
                (_matches(new_medication, a) and _matches(existing, b))
                or (_matches(new_medication, b) and _matches(existing, a))
            )
            if pair_hits:
                alerts.append({
                    "drug_a": new_medication,
                    "drug_b": existing,
                    "severity": severity,
                    "description": description,
                })
    return alerts


def check_allergy_conflict(medication_name: str, allergies: list[dict]) -> list[dict]:
    """Return allergy records whose substance overlaps with the medication name."""
    hits = []
    med_lower = medication_name.lower()
    for allergy in allergies:
        substance = (allergy.get("substance") or "").lower()
        if not substance:
            continue
        if substance in med_lower or med_lower in substance:
            hits.append(allergy)
    return hits
