"""Small curated ICD-10 code list for autocomplete/lookup. Clinicians can
still enter any code/description freely — this just speeds up common
entries and is not an official, exhaustive ICD-10/ICD-11 code set."""
from __future__ import annotations

COMMON_ICD10_CODES: list[tuple[str, str]] = [
    ("E11.9", "Type 2 diabetes mellitus without complications"),
    ("E10.9", "Type 1 diabetes mellitus without complications"),
    ("I10", "Essential (primary) hypertension"),
    ("E78.5", "Hyperlipidemia, unspecified"),
    ("J45.909", "Unspecified asthma, uncomplicated"),
    ("J44.9", "Chronic obstructive pulmonary disease, unspecified"),
    ("F41.9", "Anxiety disorder, unspecified"),
    ("F32.9", "Major depressive disorder, single episode, unspecified"),
    ("M54.5", "Low back pain"),
    ("M25.50", "Pain in unspecified joint"),
    ("K21.9", "Gastro-esophageal reflux disease without esophagitis"),
    ("N39.0", "Urinary tract infection, site not specified"),
    ("J06.9", "Acute upper respiratory infection, unspecified"),
    ("J02.9", "Acute pharyngitis, unspecified"),
    ("R51", "Headache"),
    ("R05", "Cough"),
    ("R10.9", "Unspecified abdominal pain"),
    ("E03.9", "Hypothyroidism, unspecified"),
    ("E66.9", "Obesity, unspecified"),
    ("Z00.00", "Encounter for general adult medical examination without abnormal findings"),
    ("Z23", "Encounter for immunization"),
    ("I25.10", "Atherosclerotic heart disease without angina pectoris"),
    ("I48.91", "Unspecified atrial fibrillation"),
    ("N18.9", "Chronic kidney disease, unspecified"),
    ("D64.9", "Anemia, unspecified"),
    ("G47.00", "Insomnia, unspecified"),
    ("L20.9", "Atopic dermatitis, unspecified"),
    ("M79.7", "Fibromyalgia"),
    ("K59.00", "Constipation, unspecified"),
    ("B34.9", "Viral infection, unspecified"),
]


def search_icd_codes(term: str) -> list[tuple[str, str]]:
    term = term.strip().lower()
    if not term:
        return COMMON_ICD10_CODES
    return [
        (code, desc) for code, desc in COMMON_ICD10_CODES
        if term in code.lower() or term in desc.lower()
    ]
