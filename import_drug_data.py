"""
MedQuery Drug Interactions Importer Script

Reads drug_interactions.csv using pandas, handles duplicates, orders names lexicographically,
and batch-inserts records into MySQL database via SQLAlchemy.
"""

import os
import pandas as pd
from database.connection import SessionLocal, test_db_connection
from models.drug_model import DrugInteraction

def run_import():
    """
    Parses datasets/drug_interactions.csv and batch inserts records.
    """
    csv_file = os.path.join("datasets", "drug_interactions.csv")
    if not os.path.exists(csv_file):
        print(f"Error: Target dataset not found: {csv_file}")
        return

    # Bootstrap Flask App context to initialize database tables
    from app import create_app
    app = create_app()

    with app.app_context():
        # Verify connectivity before execution
        if not test_db_connection():
            print("Error: Could not reach active database. Aborting import operations.")
            return

    print(f"Reading dataset: '{csv_file}'...")
    try:
        dataframe = pd.read_csv(csv_file)
    except Exception as read_err:
        print(f"Error: Failed to read CSV: {read_err}")
        return

    total_rows = len(dataframe)
    imported_count = 0
    skipped_count = 0
    failed_count = 0

    # Initialize DB Session
    session = SessionLocal()
    existing_pairs = set()

    # Pre-fetch existing pairs from DB for fast in-memory duplicate check
    try:
        existing_records = session.query(DrugInteraction.drug_a, DrugInteraction.drug_b).all()
        for drug_a, drug_b in existing_records:
            existing_pairs.add((drug_a.lower(), drug_b.lower()))
        print(f"Cached {len(existing_pairs)} existing drug pairings for duplicate prevention.")
    except Exception as cache_err:
        print(f"Warning: Could not pre-cache existing records: {cache_err}. Direct querying will be used.")

    batch_size = 50
    insert_queue = []

    print("Importing records in batches...")
    for index, row in dataframe.iterrows():
        try:
            drug_a = str(row.get('drug_a', '')).strip()
            drug_b = str(row.get('drug_b', '')).strip()
            severity = str(row.get('severity', 'Low')).strip()
            description = str(row.get('description', '')).strip()

            if not drug_a or not drug_b:
                print(f"Row {index} skipped: missing drug names.")
                skipped_count += 1
                continue

            # 1. Lexicographical Sorting (ensure drug_a < drug_b)
            if drug_a.lower() > drug_b.lower():
                drug_a, drug_b = drug_b, drug_a

            pair_key = (drug_a.lower(), drug_b.lower())

            # 2. Skip duplicates (either in DB or duplicated inside the CSV itself)
            if pair_key in existing_pairs:
                skipped_count += 1
                continue

            # Register pair key
            existing_pairs.add(pair_key)

            # 3. Create model instance
            interaction_record = DrugInteraction(
                drug_a=drug_a,
                drug_b=drug_b,
                severity=severity,
                description=description
            )
            insert_queue.append(interaction_record)
            imported_count += 1

            # 4. Batch Commit execution
            if len(insert_queue) >= batch_size:
                session.add_all(insert_queue)
                session.commit()
                insert_queue = []

        except Exception as row_err:
            session.rollback()
            failed_count += 1
            print(f"Error processing row {index} ({row.get('drug_a')} + {row.get('drug_b')}): {row_err}")

    # Commit remaining items in queue
    if insert_queue:
        try:
            session.add_all(insert_queue)
            session.commit()
        except Exception as final_err:
            session.rollback()
            failed_count += len(insert_queue)
            imported_count -= len(insert_queue)
            print(f"Error committing final batch: {final_err}")

    session.close()

    # Print Summary formatted report
    print("\n" + "=" * 40)
    print("           IMPORT RUN SUMMARY")
    print("=" * 40)
    print(f"Processed: {total_rows}")
    print(f"Imported:  {imported_count}")
    print(f"Skipped:   {skipped_count}")
    print(f"Failed:    {failed_count}")
    print("=" * 40 + "\n")

if __name__ == '__main__':
    run_import()
