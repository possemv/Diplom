from pathlib import Path
import pandas as pd
import pytest
import id3

DATA = Path(__file__).parent / "data" / "test_pogoda.csv"

@pytest.fixture
def df():
    return pd.DataFrame(
        {"Pogoda": ["slonecznie", "slonecznie", "pochmurnie", "deszczowo"],
         "Wiatr": ["slaby", "silny", "slaby", "slaby"],
         "Decyzja": ["tak", "nie", "tak", "tak"]},
        index=["D1", "D2", "D3", "D4"])

def test_entropy_balanced_is_one():
    d = pd.DataFrame({"Decyzja": ["tak", "nie", "tak", "nie"]})
    assert id3.entropy(d, "Decyzja") == pytest.approx(1.0)

def test_entropy_empty_is_zero(df):
    assert id3.entropy(df.iloc[0:0], "Decyzja") == 0

def test_information_gain_and_best_attribute(df):
    assert id3.information_gain(df, "Wiatr", "Decyzja") == pytest.approx(0.8113, abs=1e-3)
    assert id3.information_gain(df, "Pogoda", "Decyzja") == pytest.approx(0.3113, abs=1e-3)
    best, gain = id3.choose_best_attribute(df, ["Pogoda", "Wiatr"], "Decyzja")
    assert best == "Wiatr"

def test_tree_rules_and_stats(df):
    tree, log = id3.build_tree(df, ["Pogoda", "Wiatr"], "Decyzja")
    assert tree["attribute"] == "Wiatr"
    assert tree["branches"]["silny"] == {"is_leaf": True, "decision": "nie"}
    rules = id3.generate_rules(tree)
    assert set(rules) == {("Wiatr = slaby", "tak"), ("Wiatr = silny", "nie")}
    stats = id3.rule_statistics(rules)
    assert stats["rule_count"] == 2 and stats["max_length"] == 1
    assert id3.tree_statistics(tree) == {"internal": 1, "leaves": 2, "depth": 1}

def test_consistency():
    ok = pd.DataFrame({"A": ["x", "y"], "Decyzja": ["tak", "nie"]}, index=["R1", "R2"])
    bad = pd.DataFrame({"A": ["x", "x"], "Decyzja": ["tak", "nie"]}, index=["R1", "R2"])
    assert id3.check_consistency(ok, "Decyzja", ["A"])["is_consistent"] is True
    res = id3.check_consistency(bad, "Decyzja", ["A"])
    assert res["is_consistent"] is False
    assert res["conflicts"][0]["a"] == "R1"

def test_validate_table_empty_cells_and_size():
    d = pd.DataFrame({"A": ["x", None], "Decyzja": ["tak", "nie"]})
    assert any("puste" in p for p in id3.validate_table(d, 1000))
    full = pd.DataFrame({"A": ["x", "y"], "Decyzja": ["tak", "nie"]})
    assert any("za dużo" in p for p in id3.validate_table(full, 1))

def test_validate_decision():
    d = pd.DataFrame({"A": ["x", "y"], "Decyzja": ["tak", "tak"]})
    assert id3.validate_decision(d, "Decyzja")   # tylko jedna wartość
    assert id3.validate_decision(d, "Brak")      # nie ma takiej kolumny

def test_identifier_like_attribute_is_error():
    d = pd.DataFrame({"Id": ["1", "2", "3"], "A": ["x", "x", "y"],
                      "Decyzja": ["tak", "nie", "tak"]})
    cons = {"is_consistent": True, "conflicts": []}
    errors = id3.get_errors(d, ["Id", "A"], cons)
    assert any("'Id'" in e for e in errors)

def test_load_table_semicolon_with_index(tmp_path):
    p = tmp_path / "d.csv"
    p.write_text("Dzien;Pogoda;Decyzja\nD1;slonecznie;tak\nD2;deszczowo;nie\n", encoding="utf-8")
    d = id3.load_table(str(p), True)
    assert d.index.tolist() == ["D1", "D2"]
    assert d.columns.tolist() == ["Pogoda", "Decyzja"]

def test_pipeline_on_pogoda_file():
    d = id3.load_table(str(DATA), True).astype(str)
    decision = d.columns[-1]
    assert id3.validate_table(d, 1000) == []
    cond = id3.get_condition_cols(d, decision)
    consistency = id3.check_consistency(d, decision, cond)
    assert id3.get_errors(d, cond, consistency) == []
    tree, _ = id3.build_tree(d, cond, decision)
    rules = id3.generate_rules(tree)
    assert len(rules) > 0
    assert all(r[1] in set(d[decision]) for r in rules)