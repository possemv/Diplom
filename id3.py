import pandas as pd
import math

def load_table(file_path):
    df = pd.read_csv(file_path, index_col=0)
    decision_col = df.columns[-1]
    condition_cols = list(df.columns[:-1])
    return df, decision_col, condition_cols

def check_consistency(df, decision_col, condition_cols):
    conflicts = []
    for a in range(len(df)):
        for b in range(a + 1, len(df)):
            row1 = df.iloc[a]
            row2 = df.iloc[b]

            same_conditions = True
            for col in condition_cols:
                if row1[col] != row2[col]:
                    same_conditions = False

            different_decisions = row1[decision_col] != row2[decision_col]

            if same_conditions and different_decisions:
                conflicts.append({
                    "a": a,
                    "b": b,
                    "row1": dict(row1),
                    "row2": dict(row2),
                })
    is_consistent = len(conflicts) == 0
    return {"is_consistent": is_consistent, "conflicts": conflicts}


def table_info (df, decision_col):
    unique_values = {}
    for col in df.columns:
        unique_values[col] = df[col].unique().tolist()

    missing_values = {}
    for col in df.columns:
        missing_values[col] = int(df[col].isnull().sum())

    decisions = df[decision_col].value_counts()
    total = len(df)
    decision_distribution = []
    for class_, count in decisions.items():
        percent = round(count/total*100, 1)
        decision_distribution.append({
            "class_": class_,
            "count": int(count),
            "percent": percent
        })

    return{
        "row_count": len(df),
        "columns": df.columns.tolist(),
        "unique_values": unique_values,
        "missing_values": missing_values,
        "decision_distribution": decision_distribution,
    }

def entropy (data, decision_col):
    total = len(data)
    if total == 0:
        return 0

    result = 0
    for count in data[decision_col].value_counts():
        p = count/total
        result -= p * math.log2(p)
    return result

def information_gain(data, attribute, decision_col):
    total = len(data)
    base_entropy = entropy(data, decision_col)
    attribute_entropy = 0
    for value in data[attribute].unique():
        subset = data[data[attribute] == value]
        weight = len(subset)/total
        attribute_entropy += weight* entropy(subset, decision_col)
    return base_entropy - attribute_entropy

def choose_best_attribute(data, attributes, decision_col):
    best_attribute = attributes[0]
    best_gain = information_gain(data, attributes[0], decision_col)

    for attribute in attributes:
        gain = information_gain(data, attribute, decision_col)
        if gain > best_gain:
            best_gain = gain
            best_attribute = attribute

    return best_attribute,best_gain

def build_id3 (data, attributes, decision_col, log=None):
    if log is None:
        log = []

    if len(data[decision_col].unique()) == 1:
        decision = data[decision_col].iloc[0]
        log.append("[LIŚĆ] Decyzja:" + str(decision))
        return{
            "is_leaf": True, "decision": decision
        }

    if len(attributes) == 0:
        decision = data[decision_col].mode()[0]
        log.append("[LIŚĆ - większość] Decyzja:" + str(decision))
        return{"is_leaf": True, "decision": decision}

    best_attribute, gain = choose_best_attribute(data, attributes, decision_col)
    log.append("[WĘZEŁ] Atrybut:" + best_attribute + "(zysk = " + str(round(gain,4)) + ")")

    node = {"is_leaf": False, "attribute": best_attribute, "branches": {}}

    remaining_attributes = []
    for a in attributes:
        if a != best_attribute:
            remaining_attributes.append(a)

    for value in data[best_attribute].unique():
        subset = data[data[best_attribute] == value]
        subset = subset.drop(columns = [best_attribute])

        if len(subset) == 0:
            decision = data[decision_col].mode()[0]
            log.append(best_attribute + "=" + str(value) + "-> [LIŚĆ - pusty] Decyzja:" + str(decision))
            node["branches"][value] = {"is_leaf": True, "decision": decision}
        else:
            node["branches"][value] = build_id3(subset, remaining_attributes, decision_col, log)
    return node

def build_tree(df, condition_col, decision_col):
    log = []
    tree = build_id3(df, condition_col, decision_col, log)
    return tree, log

def generate_rules(node, path = None):
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

    return{
        "rule_count": len(rules),
        "unique_count": len(unique_rules),
        "min_length": min(lengths),
        "avg_length": round(sum(lengths)/len(lengths), 2),
        "max_length": max(lengths),
    }

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
        html = html + "<span class='edge-label'>" + str(edge_label) + "</span>"
    html = html + text
    html = html + "</div>"

    if not node["is_leaf"]:
        html = html + "<ul>"
        for value in node["branches"]:
            child = node["branches"][value]
            html = html + tree_to_html(child, value)
        html = html + "</ul>"

    html = html + "</li>"
    return html






