"""SQLite schema definition for the patient management system."""

SCHEMA_VERSION = 1

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------
-- 13. Users & Security
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    salt            TEXT NOT NULL,
    full_name       TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'clinician',
    active          INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    last_login      TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER,
    username        TEXT,
    timestamp       TEXT NOT NULL DEFAULT (datetime('now')),
    action          TEXT NOT NULL,
    entity_type     TEXT,
    entity_id       INTEGER,
    details         TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- ---------------------------------------------------------------------
-- 1. Patient Registry
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS patients (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    mrn                     TEXT NOT NULL UNIQUE,
    first_name              TEXT NOT NULL,
    last_name               TEXT NOT NULL,
    dob                     TEXT NOT NULL,
    sex                     TEXT,
    gender                  TEXT,
    phone                   TEXT,
    email                   TEXT,
    address                 TEXT,
    city                    TEXT,
    state                   TEXT,
    zip_code                TEXT,
    insurance_provider      TEXT,
    insurance_policy_number TEXT,
    insurance_group_number  TEXT,
    pcp_name                TEXT,
    pcp_contact             TEXT,
    status                  TEXT NOT NULL DEFAULT 'active',
    created_at              TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at              TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(last_name, first_name);

CREATE TABLE IF NOT EXISTS emergency_contacts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id      INTEGER NOT NULL,
    name            TEXT NOT NULL,
    relationship    TEXT,
    phone           TEXT,
    email           TEXT,
    address         TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS allergies (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id      INTEGER NOT NULL,
    substance       TEXT NOT NULL,
    reaction        TEXT,
    severity        TEXT,
    allergy_type    TEXT DEFAULT 'drug',
    status          TEXT NOT NULL DEFAULT 'active',
    noted_date      TEXT,
    notes           TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_allergies_patient ON allergies(patient_id);

-- ---------------------------------------------------------------------
-- 2. Medical History
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS medical_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id      INTEGER NOT NULL,
    category        TEXT NOT NULL,  -- past_medical, past_surgical, family, social
    description     TEXT NOT NULL,
    onset_date      TEXT,
    resolved_date   TEXT,
    status          TEXT DEFAULT 'active',
    notes           TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_history_patient ON medical_history(patient_id);

CREATE TABLE IF NOT EXISTS immunizations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id      INTEGER NOT NULL,
    vaccine         TEXT NOT NULL,
    date_given      TEXT,
    dose            TEXT,
    lot_number      TEXT,
    site            TEXT,
    provider        TEXT,
    notes           TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS medication_history (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id              INTEGER NOT NULL,
    name                    TEXT NOT NULL,
    dosage                  TEXT,
    route                   TEXT,
    frequency               TEXT,
    start_date              TEXT,
    end_date                TEXT,
    status                  TEXT DEFAULT 'active',
    prescribing_provider    TEXT,
    notes                   TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- 3. Visits / Encounters
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS visits (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id          INTEGER NOT NULL,
    visit_date          TEXT NOT NULL DEFAULT (datetime('now')),
    provider            TEXT,
    visit_type          TEXT DEFAULT 'office visit',
    chief_complaint     TEXT,
    hpi                 TEXT,
    ros                 TEXT,
    physical_exam       TEXT,
    assessment          TEXT,
    plan                TEXT,
    notes               TEXT,
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_visits_patient ON visits(patient_id, visit_date);

CREATE TABLE IF NOT EXISTS vitals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id      INTEGER NOT NULL,
    visit_id        INTEGER,
    recorded_at     TEXT NOT NULL DEFAULT (datetime('now')),
    height_cm       REAL,
    weight_kg       REAL,
    bmi             REAL,
    temp_c          REAL,
    heart_rate      INTEGER,
    resp_rate       INTEGER,
    bp_systolic     INTEGER,
    bp_diastolic    INTEGER,
    spo2            INTEGER,
    pain_score      INTEGER,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (visit_id) REFERENCES visits(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_vitals_patient ON vitals(patient_id, recorded_at);

-- ---------------------------------------------------------------------
-- 4. Diagnoses
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS diagnoses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id      INTEGER NOT NULL,
    visit_id        INTEGER,
    icd_code        TEXT NOT NULL,
    icd_system      TEXT DEFAULT 'ICD-10',
    description     TEXT NOT NULL,
    status          TEXT DEFAULT 'active',  -- active / resolved
    chronic         INTEGER DEFAULT 0,
    onset_date      TEXT,
    resolved_date   TEXT,
    notes           TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (visit_id) REFERENCES visits(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_diagnoses_patient ON diagnoses(patient_id);

-- ---------------------------------------------------------------------
-- 5. Orders & Results
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id      INTEGER NOT NULL,
    visit_id        INTEGER,
    order_type      TEXT NOT NULL,  -- lab / imaging / procedure / pathology
    order_name      TEXT NOT NULL,
    ordered_date    TEXT NOT NULL DEFAULT (datetime('now')),
    status          TEXT DEFAULT 'ordered',  -- ordered / completed / cancelled
    ordered_by      TEXT,
    notes           TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (visit_id) REFERENCES visits(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_orders_patient ON orders(patient_id);

CREATE TABLE IF NOT EXISTS results (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id            INTEGER NOT NULL,
    patient_id          INTEGER NOT NULL,
    result_name         TEXT NOT NULL,
    value               TEXT,
    numeric_value       REAL,
    unit                TEXT,
    reference_low       REAL,
    reference_high      REAL,
    abnormal_flag       TEXT,   -- normal / high / low / critical
    result_date         TEXT NOT NULL DEFAULT (datetime('now')),
    notes               TEXT,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_results_patient ON results(patient_id, result_name);

-- ---------------------------------------------------------------------
-- 6. Prescriptions
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS prescriptions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id          INTEGER NOT NULL,
    visit_id            INTEGER,
    medication_name     TEXT NOT NULL,
    dosage              TEXT,
    route               TEXT,
    frequency           TEXT,
    duration            TEXT,
    quantity            INTEGER,
    refills             INTEGER DEFAULT 0,
    refills_remaining   INTEGER DEFAULT 0,
    prescriber          TEXT,
    status              TEXT DEFAULT 'active',  -- active / completed / cancelled
    start_date          TEXT NOT NULL DEFAULT (date('now')),
    end_date            TEXT,
    notes               TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (visit_id) REFERENCES visits(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_prescriptions_patient ON prescriptions(patient_id);

-- ---------------------------------------------------------------------
-- 7. Treatment Plan
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS treatment_plans (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id      INTEGER NOT NULL,
    visit_id        INTEGER,
    therapy         TEXT,
    referral_to     TEXT,
    follow_up_date  TEXT,
    instructions    TEXT,
    goals           TEXT,
    status          TEXT DEFAULT 'open',  -- open / completed
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (visit_id) REFERENCES visits(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_plans_patient ON treatment_plans(patient_id);

-- ---------------------------------------------------------------------
-- 8. Appointments
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS appointments (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id          INTEGER NOT NULL,
    provider            TEXT,
    appt_datetime       TEXT NOT NULL,
    duration_minutes    INTEGER DEFAULT 30,
    reason              TEXT,
    status              TEXT DEFAULT 'scheduled',  -- scheduled/completed/cancelled/no-show
    reminder_sent       INTEGER DEFAULT 0,
    notes               TEXT,
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_appts_patient ON appointments(patient_id, appt_datetime);
CREATE INDEX IF NOT EXISTS idx_appts_datetime ON appointments(appt_datetime);

-- ---------------------------------------------------------------------
-- 9. Documents
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id      INTEGER NOT NULL,
    doc_type        TEXT,  -- referral / discharge_summary / consent / scan / image / other
    title           TEXT NOT NULL,
    file_path       TEXT,
    uploaded_by     TEXT,
    uploaded_at     TEXT NOT NULL DEFAULT (datetime('now')),
    notes           TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_documents_patient ON documents(patient_id);

-- ---------------------------------------------------------------------
-- 10. Billing & Administration
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS billing_claims (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id          INTEGER NOT NULL,
    visit_id            INTEGER,
    claim_date          TEXT NOT NULL DEFAULT (date('now')),
    insurance_provider  TEXT,
    cpt_codes           TEXT,
    icd_codes           TEXT,
    amount_billed       REAL DEFAULT 0,
    amount_paid         REAL DEFAULT 0,
    status              TEXT DEFAULT 'submitted',  -- submitted/paid/denied/appealed
    notes               TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (visit_id) REFERENCES visits(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_claims_patient ON billing_claims(patient_id);

CREATE TABLE IF NOT EXISTS invoices (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id      INTEGER NOT NULL,
    invoice_date    TEXT NOT NULL DEFAULT (date('now')),
    amount_due      REAL NOT NULL DEFAULT 0,
    amount_paid     REAL NOT NULL DEFAULT 0,
    status          TEXT DEFAULT 'open',  -- open/paid/overdue/void
    due_date        TEXT,
    notes           TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_invoices_patient ON invoices(patient_id);

CREATE TABLE IF NOT EXISTS payments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id      INTEGER NOT NULL,
    patient_id      INTEGER NOT NULL,
    payment_date    TEXT NOT NULL DEFAULT (date('now')),
    amount          REAL NOT NULL,
    method          TEXT,  -- cash/card/insurance/other
    notes           TEXT,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- Templates (QoL: templates for common conditions / customizable forms)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS templates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    category        TEXT NOT NULL,  -- visit_note / treatment_plan / custom_form ...
    content         TEXT NOT NULL,  -- JSON blob
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------
-- Autosave / version history (QoL)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS draft_versions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type     TEXT NOT NULL,
    entity_id       INTEGER,
    patient_id      INTEGER,
    user_id         INTEGER,
    content_json    TEXT NOT NULL,
    saved_at        TEXT NOT NULL DEFAULT (datetime('now')),
    is_autosave     INTEGER DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_drafts_entity ON draft_versions(entity_type, entity_id);

-- ---------------------------------------------------------------------
-- Full-text search index (QoL: full-text search across all records)
-- ---------------------------------------------------------------------
CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
    entity_type,
    entity_id UNINDEXED,
    patient_id UNINDEXED,
    title,
    content
);

CREATE TABLE IF NOT EXISTS schema_meta (
    key     TEXT PRIMARY KEY,
    value   TEXT
);
"""
