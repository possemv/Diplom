import os

import pandas as pd
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

import db
import id3 as logic

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

MAX_ROWS = 1000

try:
    db.create_tables()
except Exception as e:
    print('Brak połączenia z bazą danych:', e)

def get_recent():
    #zwraca (lista ostatnich tabel, czy był błąd bazy)
    try:
        return db.get_recent_tables(6), False
    except Exception as e:
        print('Nie udało się pobrać listy z bazy:', e)
        return [], True

def render_index(problems=None):
    recent_tables, db_error = get_recent()
    return render_template('index.html', problems=problems,
                           recent_tables=recent_tables, db_error=db_error)

def show_problems(problems):
    return render_index(problems)

def make_table_html(df, has_index):
    if has_index:
        table = df.reset_index()
    else:
        table = df
    return table.to_html(classes='data-table', border=0, index=False)

def load_and_check(filename, has_index):
    #wczytuje plik i sprawdza tablicę, zwraca (df, problemy)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.isfile(file_path):
        return None, ['Nie znaleziono pliku. Wgraj go ponownie.']

    try:
        df = logic.load_table(file_path, has_index)
    except pd.errors.EmptyDataError:
        return None, ['Plik jest pusty.']
    except Exception:
        return None, ['Nie udało się odczytać pliku. Sprawdź, czy to poprawny plik CSV.']

    problems = logic.validate_table(df, MAX_ROWS)
    return df, problems

def show_select_page(filename, has_index, df, problems=None):
    return render_template(
        'wybierz.html',
        filename=filename,
        has_index=has_index,
        columns=list(df.columns),
        preview=make_table_html(df.head(5), has_index),
        problems=problems,
    )

def save_to_history(filename, has_index, decision_col):
    #jeśli baza nie działa, analiza i tak ma się udać - tylko wypisujemy błąd w konsoli
    try:
        db.save_table(filename, has_index, decision_col)
    except Exception as e:
        print('Nie udało się zapisać do bazy:', e)

@app.errorhandler(413)
def file_too_big(error):
    return show_problems(['Plik jest za duży (maksymalnie 2 MB).']), 413

@app.route('/')
def index():
    return render_index()

@app.route('/wybierz', methods=['POST'])
def wybierz():
    csv_file = request.files.get('csv_file')
    if csv_file is None or csv_file.filename == '':
        return show_problems(['Nie wybrano pliku.'])
    if not csv_file.filename.lower().endswith('.csv'):
        return show_problems(['Plik musi mieć rozszerzenie .csv.'])

    filename = secure_filename(csv_file.filename)
    if filename == '':
        filename = 'dane.csv'
    csv_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    has_index = request.form.get('has_index') == '1'

    df, problems = load_and_check(filename, has_index)
    if len(problems) > 0:
        return show_problems(problems)

    return show_select_page(filename, has_index, df)

def run_analysis(filename, has_index, decision_col):
    df, problems = load_and_check(filename, has_index)
    if len(problems) > 0:
        return show_problems(problems)

    problems = logic.validate_decision(df, decision_col)
    if len(problems) > 0:
        return show_select_page(filename, has_index, df, problems)

    df = df.astype(str)

    try:
        #kolumny warunkowe
        condition_cols = logic.get_condition_cols(df, decision_col)
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
        #staty drzewa
        tree_stats = logic.tree_statistics(tree)
        #drzewo
        tree_html = "<ul class='tree'>" + logic.tree_to_html(tree) + "</ul>"
        #ostrzeżenia
        warnings = logic.get_warnings(df, condition_cols)
        if not consistency['is_consistent']:
            warnings.append('Tablica jest niespójna, drzewo może dawać niejednoznaczne decyzje.')
    except Exception:
        app.logger.exception('Błąd podczas analizy')
        return show_select_page(filename, has_index, df,
                                ['Wystąpił błąd podczas analizy. Spróbuj wybrać inną kolumnę decyzji.'])

    save_to_history(filename, has_index, decision_col)

    return render_template(
        'wyniki.html',
        filename=filename,
        decision_col=decision_col,
        table_html=make_table_html(df, has_index),
        consistency=consistency,
        info=info,
        build_log=build_log,
        tree_html=tree_html,
        tree_stats=tree_stats,
        rules=rules,
        stats=stats,
        warnings=warnings,
    )

@app.route('/analiza', methods=['POST'])
def analiza():
    filename = secure_filename(request.form.get('filename', ''))
    decision_col = request.form.get('decision_col', '')
    has_index = request.form.get('has_index') == '1'
    return run_analysis(filename, has_index, decision_col)

@app.route('/ostatnia/<int:table_id>', methods=['POST'])
def ostatnia(table_id):
    #analiza tabeli wybranej z listy ostatnich (ustawienia bierzemy z bazy)
    try:
        record = db.get_table(table_id)
    except Exception as e:
        print('Nie udało się pobrać tabeli z bazy:', e)
        return show_problems(['Nie udało się połączyć z bazą danych.'])

    if record is None:
        return show_problems(['Nie znaleziono tej tabeli w bazie.'])

    return run_analysis(record['filename'], record['has_index'], record['decision_col'])

if __name__ == '__main__':
    app.run(debug=True)