import psycopg2
import pandas as pd
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

import os

# PostgreSQL connection details from environment variables
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PORT = int(os.getenv('POSTGRES_PORT', '5432'))
PG_USER = os.getenv('POSTGRES_USER', 'postgres')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
NEW_DB_NAME = os.getenv('POSTGRES_DB', 'iris_db')

# Iris dataset URL (open source)
IRIS_CSV_URL = 'https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data'

# Table schema
CREATE_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS iris (
    id SERIAL PRIMARY KEY,
    sepal_length FLOAT,
    sepal_width FLOAT,
    petal_length FLOAT,
    petal_width FLOAT,
    species VARCHAR(50)
);
'''

def create_database():
    # Connect to default database to create a new database
    conn = psycopg2.connect(dbname='postgres', user=PG_USER, password=PG_PASSWORD, host=PG_HOST, port=PG_PORT)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{NEW_DB_NAME}'")
    exists = cur.fetchone()
    if not exists:
        cur.execute(f'CREATE DATABASE {NEW_DB_NAME}')
        print(f"Database '{NEW_DB_NAME}' created.")
    else:
        print(f"Database '{NEW_DB_NAME}' already exists.")
    cur.close()
    conn.close()

def create_table_and_insert_data():
    # Connect to the new database
    conn = psycopg2.connect(dbname=NEW_DB_NAME, user=PG_USER, password=PG_PASSWORD, host=PG_HOST, port=PG_PORT)
    cur = conn.cursor()
    cur.execute(CREATE_TABLE_SQL)
    conn.commit()
    print("Table 'iris' ensured.")

    # Download and prepare the Iris dataset
    df = pd.read_csv(IRIS_CSV_URL, header=None)
    df.columns = ['sepal_length', 'sepal_width', 'petal_length', 'petal_width', 'species']
    df = df.dropna()

    # Insert data into the table
    for _, row in df.iterrows():
        cur.execute(
            'INSERT INTO iris (sepal_length, sepal_width, petal_length, petal_width, species) VALUES (%s, %s, %s, %s, %s)',
            (row['sepal_length'], row['sepal_width'], row['petal_length'], row['petal_width'], row['species'])
        )
    conn.commit()
    print(f"Inserted {len(df)} rows into 'iris'.")
    cur.close()
    conn.close()

if __name__ == '__main__':
    try:
        create_database()
        create_table_and_insert_data()
        print(f"Setup complete. You can now connect to the '{NEW_DB_NAME}' database and use the 'iris' table.")
    except psycopg2.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
