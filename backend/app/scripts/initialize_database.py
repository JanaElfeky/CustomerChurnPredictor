#!/usr/bin/env python3
"""
Complete Database Initialization Script (FAST VERSION)

This script:
1. Tests database connection
2. Creates all tables (with option to drop/recreate)
3. Loads data using PostgreSQL COPY (10-100x faster!)
4. Verifies the data

Usage:
    python initialize_database.py                        # Load all data (FAST!)
    python initialize_database.py --sample 1000          # Load only 1000 rows
    python initialize_database.py --drop-tables          # Drop and recreate tables, then load data
    python initialize_database.py --skip-data            # Only create tables, don't load data

Schema:
    - customers: PRIMARY KEY (id) - uses ID from CSV
    - customer_labels: PRIMARY KEY (id) - uses customer ID, FOREIGN KEY to customers(id)
    - predictions: PRIMARY KEY (id) - FOREIGN KEY to customers(id)
"""

import sys
import argparse
import pandas as pd
import psycopg2
from psycopg2 import sql
import io
from sqlalchemy import text
from app import create_app, db
from app.models import Customer, CustomerLabel
from datetime import datetime
import logging
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_connection_params(app):
    """Extract PostgreSQL connection parameters from app config."""
    with app.app_context():
        database_url = app.config['SQLALCHEMY_DATABASE_URI']

    if not database_url or not database_url.startswith('postgresql://'):
        raise ValueError("DATABASE_URL must be a PostgreSQL connection string for fast loading")

    parsed = urlparse(database_url)

    return {
        'host': parsed.hostname,
        'port': parsed.port,
        'database': parsed.path[1:],  # Remove leading /
        'user': parsed.username,
        'password': parsed.password
    }


def test_connection(app):
    """Test database connection."""
    logger.info("=" * 70)
    logger.info("STEP 1: Testing Database Connection")
    logger.info("=" * 70)

    try:
        with app.app_context():
            result = db.session.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"✅ Database connected successfully!")
            logger.info(f"   PostgreSQL version: {version}")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        logger.error("\nPlease check:")
        logger.error("1. DATABASE_URL in app/config/.env")
        logger.error("2. Supabase database is running")
        logger.error("3. Network connection")
        return False


def create_tables(app, drop_existing=False):
    """Create all database tables."""
    logger.info("\n" + "=" * 70)
    logger.info("STEP 2: Creating Database Tables")
    logger.info("=" * 70)

    try:
        with app.app_context():
            # Drop existing tables if requested (to fix schema)
            if drop_existing:
                logger.info("\n⚠️  Dropping existing tables to recreate with correct schema...")
                db.session.execute(text("DROP TABLE IF EXISTS predictions CASCADE"))
                db.session.execute(text("DROP TABLE IF EXISTS customer_labels CASCADE"))
                db.session.execute(text("DROP TABLE IF EXISTS customers CASCADE"))
                db.session.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
                db.session.commit()
                logger.info("✅ Existing tables dropped")

            # Create all tables
            logger.info("\n📋 Creating tables...")
            db.create_all()

            # Check what tables exist
            result = db.session.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]

            logger.info(f"✅ Tables created/verified: {len(tables)}")
            for table in tables:
                logger.info(f"   - {table}")

            # Show primary key configuration
            logger.info("\n📊 Primary Key Configuration:")
            for table_name in ['customers', 'customer_labels', 'predictions']:
                result = db.session.execute(text(f"""
                    SELECT column_name
                    FROM information_schema.key_column_usage
                    WHERE table_name = '{table_name}' AND constraint_name LIKE '%pkey%'
                """))
                pk_cols = [row[0] for row in result.fetchall()]
                if pk_cols:
                    logger.info(f"   {table_name}: PRIMARY KEY ({', '.join(pk_cols)})")

            return True
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        return False


def load_data_fast(app, csv_path='churn.csv', max_rows=None, clear_existing=True):
    """
    Load data using PostgreSQL COPY command (10-100x faster than ORM!).

    Args:
        app: Flask application
        csv_path: Path to CSV file
        max_rows: Maximum number of rows to load (None = all)
        clear_existing: Whether to clear existing data first
    """
    logger.info("\n" + "=" * 70)
    logger.info("STEP 3: Loading Data from CSV")
    logger.info("=" * 70)

    try:
        # Read CSV
        logger.info(f"Reading: {csv_path}")
        if max_rows:
            df = pd.read_csv(csv_path, nrows=max_rows)
            logger.info(f"Loading sample: {len(df):,} rows")
        else:
            df = pd.read_csv(csv_path)
            logger.info(f"Loading all data: {len(df):,} rows")

        # Convert column names to lowercase
        df.columns = df.columns.str.lower()

        # Check for TARGET column
        has_target = 'target' in df.columns
        logger.info(f"Has labels (TARGET): {has_target}")

        if has_target:
            churn_rate = df['target'].mean()
            logger.info(f"Churn rate: {churn_rate:.2%}")
            logger.info(f"  Churned: {int(df['target'].sum()):,}")
            logger.info(f"  Not churned: {int((~df['target'].astype(bool)).sum()):,}")

        # Prepare customer data (INCLUDE ID, exclude TARGET)
        customer_cols = [col for col in df.columns if col != 'target']
        customers_df = df[customer_cols].copy()

        # Ensure 'id' column exists
        if 'id' not in customers_df.columns:
            raise ValueError("CSV must have an 'id' column")

        # Reorder columns to put 'id' first
        id_col = customers_df.pop('id')
        customers_df.insert(0, 'id', id_col)
        customer_cols = customers_df.columns.tolist()

        # Convert boolean columns properly
        bool_cols = ['pack_102', 'pack_103', 'pack_104', 'pack_105']
        for col in bool_cols:
            if col in customers_df.columns:
                customers_df[col] = customers_df[col].astype(bool)

        # Convert integer columns (CSV may have floats)
        int_cols = ['id', 'age', 'clnt_setup_tenor']  # Added 'id' to int_cols
        for col in int_cols:
            if col in customers_df.columns:
                customers_df[col] = customers_df[col].fillna(0).round().astype(int)

        # Get direct PostgreSQL connection
        logger.info("\nUsing PostgreSQL COPY for fast bulk loading...")
        logger.info("⚡ This is 10-100x faster than individual inserts!")

        conn_params = get_connection_params(app)
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()

        try:
            # Clear existing data if requested
            if clear_existing:
                logger.info("\nClearing existing data...")
                cursor.execute("DELETE FROM predictions")
                cursor.execute("DELETE FROM customer_labels")
                cursor.execute("DELETE FROM customers")
                conn.commit()
                logger.info("✅ Existing data cleared")

            # Load customers using COPY in batches (to avoid timeouts)
            logger.info(f"\nLoading {len(customers_df):,} customers...")

            # Build column list
            columns_sql = sql.SQL(', ').join(map(sql.Identifier, customer_cols))
            copy_sql = sql.SQL("COPY customers ({}) FROM STDIN WITH (FORMAT CSV, NULL '\\N')").format(columns_sql)

            start_time = datetime.now()
            batch_size = 50000  # Load 50k rows at a time to avoid timeout
            total_batches = (len(customers_df) + batch_size - 1) // batch_size

            for batch_num in range(total_batches):
                start_idx = batch_num * batch_size
                end_idx = min((batch_num + 1) * batch_size, len(customers_df))
                batch_df = customers_df.iloc[start_idx:end_idx]

                logger.info(f"  Batch {batch_num + 1}/{total_batches}: rows {start_idx:,} to {end_idx:,}")

                # Create buffer for this batch
                buffer = io.StringIO()
                batch_df.to_csv(buffer, index=False, header=False, na_rep='\\N')
                buffer.seek(0)

                # Load this batch
                cursor.copy_expert(copy_sql, buffer)
                conn.commit()

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Customers loaded in {elapsed:.2f} seconds!")
            logger.info(f"   Speed: {int(len(customers_df)/elapsed):,} rows/second")

            # Use the customer IDs from the CSV we just loaded
            customer_ids = customers_df['id'].tolist()
            logger.info(f"\n✅ Loaded customers with IDs from CSV (first ID: {customer_ids[0]:,}, last ID: {customer_ids[-1]:,})")

            # Load labels if TARGET exists
            if has_target:
                logger.info(f"\nLoading {len(df):,} labels...")
                start_time = datetime.now()

                # Prepare labels dataframe using the same IDs from CSV
                labels_df = pd.DataFrame({
                    'id': df['id'].astype(int),  # Use original IDs from CSV
                    'target': df['target'].astype(bool),
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                })

                # Load labels in batches
                batch_size = 50000
                total_batches = (len(labels_df) + batch_size - 1) // batch_size

                for batch_num in range(total_batches):
                    start_idx = batch_num * batch_size
                    end_idx = min((batch_num + 1) * batch_size, len(labels_df))
                    batch_df = labels_df.iloc[start_idx:end_idx]

                    logger.info(f"  Batch {batch_num + 1}/{total_batches}: rows {start_idx:,} to {end_idx:,}")

                    # Create buffer for this batch
                    buffer = io.StringIO()
                    batch_df.to_csv(buffer, index=False, header=False)
                    buffer.seek(0)

                    # COPY labels
                    cursor.copy_expert(
                        """
                        COPY customer_labels (id, target, created_at, updated_at)
                        FROM STDIN
                        WITH (FORMAT CSV)
                        """,
                        buffer
                    )

                    conn.commit()

                elapsed = (datetime.now() - start_time).total_seconds()
                logger.info(f"✅ Labels loaded in {elapsed:.2f} seconds!")
                logger.info(f"   Speed: {int(len(labels_df)/elapsed):,} rows/second")

            logger.info("\n✅ Data loading complete!")
            return True

        finally:
            cursor.close()
            conn.close()

    except FileNotFoundError:
        logger.error(f"❌ CSV file not found: {csv_path}")
        return False
    except Exception as e:
        logger.error(f"❌ Data loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_data(app):
    """Verify data was loaded correctly."""
    logger.info("\n" + "=" * 70)
    logger.info("STEP 4: Verifying Data")
    logger.info("=" * 70)

    try:
        with app.app_context():
            # Count records
            customer_count = Customer.query.count()
            label_count = CustomerLabel.query.count()

            logger.info(f"✅ Verification complete!")
            logger.info(f"   Total customers: {customer_count:,}")
            logger.info(f"   Total labels: {label_count:,}")

            if label_count > 0:
                # Check label distribution
                churned = CustomerLabel.query.filter_by(target=True).count()
                not_churned = CustomerLabel.query.filter_by(target=False).count()

                logger.info(f"\n   Label distribution:")
                logger.info(f"     Churned: {churned:,} ({churned/label_count*100:.2f}%)")
                logger.info(f"     Not churned: {not_churned:,} ({not_churned/label_count*100:.2f}%)")

            # Show sample customer
            sample = Customer.query.first()
            if sample:
                logger.info(f"\n   Sample customer ID: {sample.id}")
                logger.info(f"     Age: {sample.age}")
                logger.info(f"     Tenure: {sample.clnt_setup_tenor} months")

            return True

    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Initialize database and load churn data (FAST!)',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--csv',
        default='churn.csv',
        help='Path to CSV file (default: churn.csv)'
    )
    parser.add_argument(
        '--sample',
        type=int,
        help='Load only N rows (for testing)'
    )
    parser.add_argument(
        '--skip-data',
        action='store_true',
        help='Skip data loading (only create tables)'
    )
    parser.add_argument(
        '--keep-existing',
        action='store_true',
        help='Keep existing data (append instead of replace)'
    )
    parser.add_argument(
        '--drop-tables',
        action='store_true',
        help='Drop and recreate tables (fixes schema issues)'
    )

    args = parser.parse_args()

    # Print banner
    print("\n" + "=" * 70)
    print("DATABASE INITIALIZATION SCRIPT (FAST VERSION)")
    print("=" * 70)
    print(f"CSV file: {args.csv}")
    if args.sample:
        print(f"Sample size: {args.sample:,} rows")
    else:
        print("Loading: ALL data")
    print(f"Clear existing: {not args.keep_existing}")
    print(f"Drop tables: {args.drop_tables}")
    print(f"Method: PostgreSQL COPY (⚡ 10-100x faster!)")
    print("=" * 70)

    if not args.skip_data or args.drop_tables:
        print("\n⚠️  This will modify your Supabase database!")
        if args.drop_tables:
            print("⚠️  All tables will be DROPPED and RECREATED!")
        if not args.keep_existing:
            print("⚠️  Existing data will be DELETED!")
        print("\nPress Enter to continue or Ctrl+C to cancel...")
        input()

    # Create app
    app = create_app()

    # Step 1: Test connection
    if not test_connection(app):
        logger.error("\n❌ FAILED: Cannot connect to database")
        sys.exit(1)

    # Step 2: Create tables
    if not create_tables(app, drop_existing=args.drop_tables):
        logger.error("\n❌ FAILED: Cannot create tables")
        sys.exit(1)

    # Step 3: Load data (unless skipped)
    if not args.skip_data:
        if not load_data_fast(
            app,
            csv_path=args.csv,
            max_rows=args.sample,
            clear_existing=not args.keep_existing
        ):
            logger.error("\n❌ FAILED: Data loading failed")
            sys.exit(1)
    else:
        logger.info("\n⏭️  Data loading skipped")

    # Step 4: Verify
    if not verify_data(app):
        logger.error("\n❌ FAILED: Verification failed")
        sys.exit(1)

    # Success!
    logger.info("\n" + "=" * 70)
    logger.info("✅ DATABASE INITIALIZATION COMPLETE!")
    logger.info("=" * 70)
    logger.info("\nNext steps:")
    logger.info("1. Start server: python run.py")
    logger.info("2. Test API: python test_api_automation.py")
    logger.info("3. View data in Supabase Dashboard → Table Editor")


if __name__ == "__main__":
    main()
