import psycopg2
import os
from configs import init_config_postgres

params = init_config_postgres()

TABLE = 'products'


def connect_db():
    conn = None
    try:
        conn = psycopg2.connect(**params)
    finally:
        return conn


def db_exists(cursor):
    cursor.execute(
        "select exists"
        "(select * from information_schema.tables where table_name=%s)",
        ('products',)
    )
    return cursor.fetchone()[0]


def create_table(cursor):
    cursor.execute(
        "CREATE TABLE products (id serial PRIMARY KEY, name varchar, "
        "brand varchar, details varchar, price real, size varchar, "
        "is_by_weight bool);")


def save_df(df):
    if conn := connect_db():
        tmp_f = "./products.csv"
        df.to_csv(tmp_f, index=False, header=False, sep='|', encoding='utf8')
        file = open(tmp_f, 'r', encoding='utf8')
        cursor = conn.cursor()
        try:
            if not db_exists(cursor):
                create_table(cursor)
                conn.commit()
            cursor.copy_from(
                file,
                TABLE,
                sep="|",
                columns=tuple(df.columns)
            )
            conn.commit()

        except (Exception, psycopg2.DatabaseError) as error:
            print("Error: %s" % error)
            conn.rollback()

        finally:
            file.close()
            cursor.close()
            os.remove(tmp_f)
            conn.close()
