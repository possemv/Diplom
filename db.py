import psycopg2
import config

def get_connection():
    return psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
    )


def create_tables():
    #tworzy tabelę, jeśli jeszcze jej nie ma
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS recent_tables (
            id SERIAL PRIMARY KEY,
            filename TEXT NOT NULL UNIQUE,
            has_index BOOLEAN NOT NULL,
            decision_col TEXT NOT NULL,
            last_used TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


def save_table(filename, has_index, decision_col):
    #zapisuje tabelę; jeśli plik o tej nazwie już jest, tylko aktualizuje wpis
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO recent_tables (filename, has_index, decision_col, last_used)
        VALUES (%s, %s, %s, NOW())
        ON CONFLICT (filename) DO UPDATE
        SET has_index = EXCLUDED.has_index,
            decision_col = EXCLUDED.decision_col,
            last_used = NOW()
    """, (filename, has_index, decision_col))
    conn.commit()
    cur.close()
    conn.close()


def get_recent_tables(limit=6):
    #zwraca listę ostatnio używanych tabel (najnowsze na początku)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, filename, has_index, decision_col, last_used
        FROM recent_tables
        ORDER BY last_used DESC
        LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    tables = []
    for row in rows:
        tables.append({
            "id": row[0],
            "filename": row[1],
            "has_index": row[2],
            "decision_col": row[3],
            "last_used": row[4],
        })
    return tables


def get_table(table_id):
    #zwraca jeden wpis albo None, jeśli nie ma takiego id
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, filename, has_index, decision_col
        FROM recent_tables
        WHERE id = %s
    """, (table_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row is None:
        return None
    return {"id": row[0], "filename": row[1], "has_index": row[2], "decision_col": row[3]}