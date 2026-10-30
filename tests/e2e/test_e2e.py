import os
import re
from pathlib import Path
from playwright.sync_api import Page, expect

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:5000")
CSV = str(Path(__file__).parent.parent / "data" / "test_pogoda.csv")

def test_upload_analyse_and_see_tree_and_rules(page: Page):
    page.goto(BASE)
    page.set_input_files("input[name=csv_file]", CSV)
    page.get_by_role("button", name="Dalej").click()

    expect(page.get_by_role("heading", name="Wybierz kolumnę decyzji")).to_be_visible()
    page.get_by_role("button", name="Analizuj").click()

    expect(page.get_by_role("heading", name=re.compile("Wyniki analizy"))).to_be_visible()

    page.get_by_role("button", name="Drzewo").click()
    expect(page.locator(".tree")).to_be_visible()

    page.get_by_role("button", name="Reguły").click()
    expect(page.locator("#reguly li").first).to_contain_text("THEN Decyzja")