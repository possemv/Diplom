import math
from html import escape

import numpy as np
import pandas as pd

def load_table(file_path, has_index=True):
    if has_index:
        index_col = 0
    else:
        index_col = None

    try:
        df = pd.read_csv(file_path, sep=None, engine="python",
                         index_col=index_col, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, sep=None, engine="python",
                         index_col=index_col, encoding="cp1250")

    #puste - brak danych
    df.columns = df.columns.astype(str).str.strip()
    for col in df.columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].str.strip()
            df[col] = df[col].replace("", np.nan)

    if not has_index:
        df.index = range(1, len(df) + 1)
    return df


def validate_table(df, max_rows):
    problems = []

    if len(df.columns) < 2:
        problems.append("Tablica musi mieć co najmniej 2 kolumny (warunki i decyzję).")
    if len(df) > max_rows:
        problems.append("Tablica ma za dużo wierszy (" + str(len(df)) + "). Maksymalnie: " + str(max_rows) + ".")

    #puste komórki
    details = []
    for col in df.columns:
        missing_rows = df[df[col].isnull()].index.tolist()
        if len(missing_rows) > 0:
            names = []
            for row in missing_rows:
                names.append(str(row))
            text = ", ".join(names[:10])
            if len(names) > 10:
                text = text + " ..."
            details.append("Kolumna '" + col + "': brak danych w wierszach: " + text)
    if df.index.isnull().any():
        details.append("Pierwsza kolumna jako nazwa wierszy ma puste komórki.")

    if len(details) > 0:
        problems.append("Tablica zawiera puste komórki.")
        problems = problems + details

    return problems


def validate_decision(df, decision_col):
    problems = []
    if decision_col not in df.columns:
        problems.append("Wybrana kolumna decyzji nie istnieje w tablicy.")
    elif df[decision_col].nunique() < 2:
        problems.append("Kolumna '" + decision_col + "' ma tylko jedną wartość, czyli nie ma możliwości zbudować drzewa.")
    return problems


def get_condition_cols(df, decision_col):
    condition_cols = []
    for col in df.columns:
        if col != decision_col:
            condition_cols.append(col)
    return condition_cols


def get_errors(df, condition_cols, consistency):
    errors = []
    if not consistency["is_consistent"]:
        errors.append("Tablica jest niespójna. Wierszy z takimi samymi warunkami mają różne decyzje. Liczba konfliktów: " + str(len(consistency["conflicts"])))

    for col in condition_cols:
        if df[col].nunique() == len(df):
            errors.append("Atrybut '" + col + "' ma inną wartość w każdym wierszu, wygląda jak identyfikator.")
    return errors


def check_consistency(df, decision_col, condition_cols):
    #dwa wiersze maja to samo but różne decyzji
    rows = df.to_dict("records")
    names = df.index.tolist()
    conflicts = []

    for a in range(len(rows)):
        for b in range(a + 1, len(rows)):
            row1 = rows[a]
            row2 = rows[b]

            same_conditions = True
            for col in condition_cols:
                if row1[col] != row2[col]:
                    same_conditions = False
                    break

            different_decisions = row1[decision_col] != row2[decision_col]

            if same_conditions and different_decisions:
                conflicts.append({
                    "a": names[a],
                    "b": names[b],
                    "row1": row1,
                    "row2": row2,
                })

    is_consistent = len(conflicts) == 0
    return {"is_consistent": is_consistent, "conflicts": conflicts}


def table_info(df, decision_col):
    unique_values = {}
    for col in df.columns:
        unique_values[col] = df[col].unique().tolist()

    decisions = df[decision_col].value_counts()
    total = len(df)
    decision_distribution = []
    for class_, count in decisions.items():
        percent = round(count / total * 100, 1)
        decision_distribution.append({
            "class_": class_,
            "count": int(count),
            "percent": percent,
        })

    return {
        "row_count": len(df),
        "columns": df.columns.tolist(),
        "unique_values": unique_values,
        "decision_distribution": decision_distribution,
    }

def entropy(data, decision_col):
    total = len(data)
    if total == 0:
        return 0

    result = 0
    for count in data[decision_col].value_counts():
        p = count / total
        result -= p * math.log2(p)
    return result

def information_gain(data, attribute, decision_col):
    total = len(data)
    base_entropy = entropy(data, decision_col)
    attribute_entropy = 0
    for value in data[attribute].unique():
        subset = data[data[attribute] == value]
        weight = len(subset) / total
        attribute_entropy += weight * entropy(subset, decision_col)
    return base_entropy - attribute_entropy

def choose_best_attribute(data, attributes, decision_col):
    best_attribute = attributes[0]
    best_gain = information_gain(data, attributes[0], decision_col)

    for attribute in attributes:
        gain = information_gain(data, attribute, decision_col)
        if gain > best_gain:
            best_gain = gain
            best_attribute = attribute

    return best_attribute, best_gain

def build_id3(data, attributes, decision_col, log=None):
    if log is None:
        log = []

    if len(data[decision_col].unique()) == 1:
        decision = data[decision_col].iloc[0]
        log.append("[LIŚĆ] Decyzja: " + str(decision))
        return {"is_leaf": True, "decision": decision}

    if len(attributes) == 0:
        decision = data[decision_col].mode()[0]
        log.append("[LIŚĆ - większość] Decyzja: " + str(decision))
        return {"is_leaf": True, "decision": decision}

    best_attribute, gain = choose_best_attribute(data, attributes, decision_col)
    log.append("[WĘZEŁ] Atrybut: " + best_attribute + " (zysk = " + str(round(gain, 4)) + ")")

    node = {"is_leaf": False, "attribute": best_attribute, "branches": {}}

    remaining_attributes = []
    for a in attributes:
        if a != best_attribute:
            remaining_attributes.append(a)

    for value in data[best_attribute].unique():
        subset = data[data[best_attribute] == value]
        subset = subset.drop(columns=[best_attribute])

        if len(subset) == 0:
            decision = data[decision_col].mode()[0]
            log.append(best_attribute + " = " + str(value) + " -> [LIŚĆ - pusty] Decyzja: " + str(decision))
            node["branches"][value] = {"is_leaf": True, "decision": decision}
        else:
            node["branches"][value] = build_id3(subset, remaining_attributes, decision_col, log)
    return node


def build_tree(df, condition_cols, decision_col):
    log = []
    tree = build_id3(df, condition_cols, decision_col, log)
    return tree, log

def generate_rules(node, path=None):
    if path is None:
        path = []

    rules = []
    if node["is_leaf"]:
        condition = ""
        for i in range(len(path)):
            attribute, value = path[i]
            if i > 0:
                condition += " AND "
            condition += attribute + " = " + str(value)
        rules.append((condition, node["decision"]))
    else:
        for value in node["branches"]:
            child_node = node["branches"][value]
            new_path = path + [(node["attribute"], value)]
            rules += generate_rules(child_node, new_path)
    return rules

def rule_statistics(rules):
    lengths = []
    for rule in rules:
        condition = rule[0]
        condition_count = len(condition.split(" AND "))
        lengths.append(condition_count)

    unique_rules = set()
    for rule in rules:
        unique_rules.add(rule[0])

    return {
        "rule_count": len(rules),
        "unique_count": len(unique_rules),
        "min_length": min(lengths),
        "avg_length": round(sum(lengths) / len(lengths), 2),
        "max_length": max(lengths),
    }

def tree_statistics(node):
    #liczy węzły, liście i głębokość drzewa
    if node["is_leaf"]:
        return {"internal": 0, "leaves": 1, "depth": 0}

    internal = 1
    leaves = 0
    max_child_depth = 0
    for value in node["branches"]:
        child = tree_statistics(node["branches"][value])
        internal += child["internal"]
        leaves += child["leaves"]
        if child["depth"] > max_child_depth:
            max_child_depth = child["depth"]

    return {"internal": internal, "leaves": leaves, "depth": max_child_depth + 1}

def tree_to_html(node, edge_label=None):
    if node["is_leaf"]:
        box_class = "leaf"
        text = "Decyzja: " + str(node["decision"])
    else:
        box_class = "attr"
        text = node["attribute"]

    html = "<li>"
    html = html + "<div class='node-box " + box_class + "'>"
    if edge_label is not None:
        html = html + "<span class='edge-label'>" + escape(str(edge_label)) + "</span>"
    html = html + escape(text)
    html = html + "</div>"

    if not node["is_leaf"]:
        html = html + "<ul>"
        for value in node["branches"]:
            child = node["branches"][value]
            html = html + tree_to_html(child, value)
        html = html + "</ul>"

    html = html + "</li>"
    return html