import io
import pytest
import app as webapp

GOOD = ("Dzien,Pogoda,Wiatr,Decyzja\nD1,slonecznie,slaby,tak\nD2,slonecznie,silny,nie\n"
        "D3,pochmurnie,slaby,tak\nD4,deszczowo,slaby,tak\nD5,deszczowo,silny,nie\n")
CONFLICT = "Dzien,A,Decyzja\nR1,x,tak\nR2,x,nie\nR3,y,tak\n"

@pytest.fixture
def client(tmp_path, monkeypatch):
    # testy tras nie dotykają prawdziwej bazy danych
    monkeypatch.setattr(webapp.db, "save_table", lambda *a, **k: None)
    monkeypatch.setattr(webapp.db, "get_recent_tables", lambda *a, **k: [])
    webapp.app.config["TESTING"] = True
    webapp.app.config["UPLOAD_FOLDER"] = str(tmp_path)
    return webapp.app.test_client()

def upload(client, name, content):
    return client.post(
        "/wybierz",
        data={"csv_file": (io.BytesIO(content.encode("utf-8")), name), "has_index": "1"},
        content_type="multipart/form-data")

def text(resp):
    return resp.get_data(as_text=True)

def test_index_page(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Indukcja reguł" in text(r)

def test_no_file(client):
    assert "Nie wybrano pliku" in text(client.post("/wybierz", data={}))

def test_wrong_extension(client):
    assert ".csv" in text(upload(client, "dane.txt", GOOD))

def test_full_flow(client):
    assert "Wybierz kolumnę decyzji" in text(upload(client, "dane.csv", GOOD))
    r = client.post("/analiza", data={"filename": "dane.csv", "has_index": "1",
                                      "decision_col": "Decyzja"})
    page = text(r)
    assert "Wyniki analizy" in page
    assert "THEN Decyzja = nie" in page

def test_inconsistent_table_stops_analysis(client):
    upload(client, "konflikt.csv", CONFLICT)
    r = client.post("/analiza", data={"filename": "konflikt.csv", "has_index": "1",
                                      "decision_col": "Decyzja"})
    assert "Analiza została zatrzymana" in text(r)