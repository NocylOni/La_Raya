# Patient Management System

A desktop patient management application built with Python, Tkinter and
SQLite. Everything runs locally — no server, no internet connection
required, all data stored in a single SQLite database file on your PC.

## Features

1. **Patient Registry** — demographics, contact info, insurance, emergency
   contacts, allergies, primary care physician.
2. **Medical History** — past medical/surgical history, family history,
   social history, medication history, immunizations.
3. **Visits / Encounters** — SOAP notes (chief complaint, HPI, ROS, physical
   exam, assessment, plan) plus vital signs with trend graphs.
4. **Diagnoses** — ICD-10/ICD-11 codes with lookup, problem list, chronic
   condition tracking, active/resolved status.
5. **Orders & Results** — labs, imaging, procedures, pathology, with
   results, reference ranges, abnormal flagging and trend graphs.
6. **Prescriptions** — dosage, duration, refills, medication history, with
   drug-interaction and allergy alerts when prescribing.
7. **Treatment Plan** — therapies, referrals, follow-up dates, patient
   instructions, goals.
8. **Appointments** — scheduling, rescheduling, cancellations, no-shows,
   today's/upcoming appointment views.
9. **Documents** — referrals, discharge summaries, consent forms, scans,
   images; files are copied into the app's managed data folder.
10. **Billing & Administration** — insurance claims, invoices, payments,
    CPT/ICD coding, balance due.
11. **Clinical Timeline** — chronological view of visits, diagnoses,
    medications, orders/results and appointments for a patient.
12. **Reporting & Analytics** — patient summaries (PDF export), clinic
    statistics, disease registries.
13. **User & Security** — multiple accounts with roles, audit log,
    PBKDF2-hashed passwords, one-click database backups.

Quality-of-life features: fast patient search, full-text search across all
records, templates for common visit notes, autosave/version history,
vitals & lab trend graphs, clinical alerts (drug interactions, allergy
conflicts, abnormal labs, overdue follow-ups), and PDF export.

## Running from source

Requires Python 3.10+ with Tkinter (on Debian/Ubuntu: `sudo apt install
python3-tk`; on Windows/macOS the official python.org installer already
includes it).

```bash
cd patient_management
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

On first launch a default administrator account is created:

- **Username:** `admin`
- **Password:** `admin123`

Change this password immediately from the Admin tab after first login.

Application data (database, backups, uploaded documents) is stored under:

- Windows: `%APPDATA%\PatientManagement`
- macOS/Linux: `~/.patient_management`

## Running the tests

```bash
pip install -r requirements.txt
pytest app/tests/
```

The GUI smoke tests require a display; on a headless Linux machine install
`xvfb` and run `xvfb-run -a pytest app/tests/`.

## Building a standalone executable

PyInstaller must run on the same OS you want the executable for (it does
not cross-compile). To build on the machine you'll actually run the app on:

**Windows:** double-click `build.bat` (or run it from a Command Prompt in
this folder). This creates `dist\PatientManagement.exe` — a single file
you can copy anywhere and double-click to run, no Python installation
needed on the target machine.

**macOS / Linux:**

```bash
./build.sh
```

This creates `dist/PatientManagement`.

Both scripts create their own build virtual environment, install
dependencies, and run PyInstaller using the included `PatientManagement.spec`.
You can also run PyInstaller manually:

```bash
pip install -r requirements.txt
pyinstaller PatientManagement.spec --noconfirm
```

The resulting executable is self-contained (Python interpreter, Tkinter,
matplotlib and reportlab are all bundled) — it can be copied to another
machine of the same OS without installing anything else.

## Project layout

```
patient_management/
  run.py                  entry point used directly and by PyInstaller
  PatientManagement.spec  PyInstaller build spec
  app/
    db/                   SQLite schema, connection management, DAOs
    logic/                alerts, drug interactions, ICD codes, PDF export
    gui/                  Tkinter windows and per-module tabs
    tests/                pytest suite (DAO/logic tests + GUI smoke tests)
```
