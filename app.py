import os

import id3 as logic
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/analiza', methods = ["POST"])
def analiza():
    csv_file = request.files.get('csv_file')
    if csv_file is None or csv_file.filename == "":
        return redirect(url_for('index'))

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], csv_file.filename)
    csv_file.save(file_path)

    #wczytanie
    df, decision_col, condition_cols = logic.load_table(file_path)
    #spójność
    consistency = logic.check_consistency(df, decision_col, condition_cols)
    #info tabl
    info = logic.table_info(df, decision_col)
    #drzewo id3
    tree, build_log = logic.build_tree(df, condition_cols, decision_col)
    #reguły
    rules = logic.generate_rules(tree)
    #staty reguł
    stats = logic.rule_statistics(rules)
    #drzewo
    tree_html = "<ul class ='tree'>" + logic.tree_to_html(tree) + "</ul>"

    return render_template(
        'wyniki.html',
        filename = csv_file.filename,
        table_html=df.reset_index().to_html(classes="data-table", border=0, index=False),
        consistency = consistency,
        info = info,
        build_log = build_log,
        rules = rules,
        stats = stats,
        tree_html = tree_html,
    )
if __name__ == "__main__":
    app.run(debug = True)





