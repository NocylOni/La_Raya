import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from app.db.database import Database


@pytest.fixture()
def db(tmp_path):
    database = Database(tmp_path / "test.db")
    yield database
    database.close()


@pytest.fixture()
def patient_id(db):
    from app.db.dao import patients
    return patients.create_patient(
        db, first_name="Jane", last_name="Doe", dob="1985-04-12", sex="F",
        phone="555-1234", email="jane@example.com",
    )
