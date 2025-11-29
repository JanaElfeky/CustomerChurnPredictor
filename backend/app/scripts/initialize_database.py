"""
Initialize database: create tables and load CSV data.
"""

import sys
import pandas as pd
import psycopg2
from psycopg2 import sql
import io
from sqlalchemy import text
from app import create_app, db
from datetime import datetime
from urllib.parse import urlparse


def get_connection_params(app):
    """Extract PostgreSQL connection parameters from app config."""
    with app.app_context():
        database_url = app.config['SQLALCHEMY_DATABASE_URI']

    if not database_url or not database_url.startswith('postgresql://'):
        raise ValueError("DATABASE_URL must be a PostgreSQL connection string")

    parsed = urlparse(database_url)
    return {
        'host': parsed.hostname,
        'port': parsed.port,
        'database': parsed.path[1:],
        'user': parsed.username,
        'password': parsed.password
    }


def create_tables(app):
    """Create all database tables."""
    print("\nCreating tables...")

    with app.app_context():
        db.session.execute(text("DROP TABLE IF EXISTS predictions CASCADE"))
        db.session.execute(
            text("DROP TABLE IF EXISTS customer_labels CASCADE"))
        db.session.execute(text("DROP TABLE IF EXISTS customers CASCADE"))
        db.session.commit()

        db.create_all()

    print("Tables created successfully")


def load_csv_data(app, csv_path='churn.csv'):
    """Load data from CSV using PostgreSQL COPY."""
    print(f"\nLoading data from {csv_path}...")

    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.lower()

    has_target = 'target' in df.columns
    customer_cols = [col for col in df.columns if col != 'target']
    customers_df = df[customer_cols].copy()

    if 'id' not in customers_df.columns:
        raise ValueError("CSV must have an 'id' column")

    # Ensure id is first column
    id_col = customers_df.pop('id')
    customers_df.insert(0, 'id', id_col)
    customer_cols = customers_df.columns.tolist()

    # Type conversions
    bool_cols = ['pack_102', 'pack_103', 'pack_104', 'pack_105']
    for col in bool_cols:
        if col in customers_df.columns:
            customers_df[col] = customers_df[col].astype(bool)

    int_cols = ['id', 'age', 'clnt_setup_tenor']
    for col in int_cols:
        if col in customers_df.columns:
            customers_df[col] = customers_df[col].fillna(0).round().astype(int)

    conn_params = get_connection_params(app)
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()

    try:
        # Load customers
        print(f"Loading {len(customers_df):,} customers...")

        columns_sql = sql.SQL(', ').join(map(sql.Identifier, customer_cols))
        copy_sql = sql.SQL(
            "COPY customers ({}) FROM STDIN WITH (FORMAT CSV, NULL '\\N')").format(columns_sql)

        buffer = io.StringIO()
        customers_df.to_csv(buffer, index=False, header=False, na_rep='\\N')
        buffer.seek(0)

        cursor.copy_expert(copy_sql, buffer)
        conn.commit()
        print("Customers loaded")

        # Load labels if present
        if has_target:
            print(f"Loading {len(df):,} labels...")

            labels_df = pd.DataFrame({
                'id': df['id'].astype(int),
                'target': df['target'].astype(bool),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            })

            buffer = io.StringIO()
            labels_df.to_csv(buffer, index=False, header=False)
            buffer.seek(0)

            cursor.copy_expert(
                """
                COPY customer_labels (id, target, created_at, updated_at)
                FROM STDIN WITH (FORMAT CSV)
                """,
                buffer
            )
            conn.commit()
            print("Labels loaded")

        print("\nData loading complete")

    finally:
        cursor.close()
        conn.close()


def main():
    """Main execution."""
    csv_path = sys.argv[1] if len(sys.argv) > 1 else 'churn.csv'

    print("=" * 50)
    print("DATABASE INITIALIZATION")
    print("=" * 50)
    print(f"CSV: {csv_path}")
    print("\nThis will DROP existing tables and load new data")
    print("Press Enter to continue or Ctrl+C to cancel...")
    input()

    app = create_app()

    try:
        create_tables(app)
        load_csv_data(app, csv_path)

        print("\n" + "=" * 50)
        print("INITIALIZATION COMPLETE")
        print("=" * 50)

    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
