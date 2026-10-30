import pytest
import db

PREFIX = "pytest_"   # testy ruszają tylko wpisy o takich nazwach, nie Twoje prawdziwe dane

def _cleanup():
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM recent_tables WHERE filename LIKE 'pytest\\_%'")
    conn.commit()
    cur.close()
    conn.close()

@pytest.fixture(autouse=True)
def clean():
    try:
        db.create_tables()
        _cleanup()
    except Exception:
        pytest.skip("Brak połączenia z bazą danych PostgreSQL")
    yield
    _cleanup()

def _mine():
    return [t for t in db.get_recent_tables(1000) if t["filename"].startswith(PREFIX)]

def test_save_and_list():
    db.save_table(PREFIX + "a.csv", True, "Decyzja")
    rows = _mine()
    assert len(rows) == 1
    assert rows[0]["filename"] == PREFIX + "a.csv"
    assert rows[0]["decision_col"] == "Decyzja"

def test_same_file_twice_updates_instead_of_duplicate():
    db.save_table(PREFIX + "a.csv", True, "Decyzja")
    db.save_table(PREFIX + "a.csv", False, "Wynik")
    rows = _mine()
    assert len(rows) == 1
    assert rows[0]["decision_col"] == "Wynik"

def test_get_table():
    db.save_table(PREFIX + "a.csv", True, "Decyzja")
    rec = db.get_table(_mine()[0]["id"])
    assert rec["filename"] == PREFIX + "a.csv"
    assert rec["has_index"] is True
    assert db.get_table(999999999) is None