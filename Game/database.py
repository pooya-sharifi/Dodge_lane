#! /bin/python3
import sqlite3

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Exception as e:
        print(e)

    return conn


def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Exception as e:
        print(e)




def insert_new_record(name, score):
    insert_query = f"""INSERT INTO scores VALUES ("{name}", {score});"""

    sort_query = """SELECT * FROM scores ORDER BY score DESC;"""

    conn = create_connection("scores.db")

    try:
        c = conn.cursor()
        c.execute(sort_query)
        rows = c.fetchall()
        
        rank = len(rows)
        for i, (n, s) in enumerate(rows):
            if score > s:
                rank = i
                break
        c.execute(insert_query)
        conn.commit()
    except Exception as e:
        print(e)

    return rank + 1


if __name__ == '__main__':
    conn = create_connection("scores.db")

    table_query = """CREATE TABLE IF NOT EXISTS scores (
                                    name text NOT NULL,
                                    score integer
                                );"""
    

    if conn is not None:
        create_table(conn, table_query)
    else:
        print("DB connection failed")