"""
Upload Unk Dictionary to BigQuery
=================================
Uploads the generated JSON dictionary to a BigQuery table.
"""

import os
import json
from google.cloud import bigquery
from google.api_core.exceptions import NotFound

# Configuration
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "unk-app-480102")
DATASET_ID = "unk_knowledge_base"
TABLE_ID = "slang_dictionary"
JSON_FILE = "unk_dictionary_seed.json"

def upload_to_bigquery():
    client = bigquery.Client(project=PROJECT_ID)
    
    # 1. Create Dataset if not exists
    dataset_ref = client.dataset(DATASET_ID)
    try:
        client.get_dataset(dataset_ref)
        print(f"Dataset {DATASET_ID} already exists.")
    except NotFound:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "US"
        client.create_dataset(dataset)
        print(f"Created dataset {DATASET_ID}.")

    # 2. Define Schema
    schema = [
        bigquery.SchemaField("term", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("definition", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("unk_translation", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("example_usage", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("category", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("origin_era", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("target_audience_relevance", "STRING", mode="NULLABLE"),
    ]
    
    table_ref = dataset_ref.table(TABLE_ID)
    
    # 3. Create Table if not exists (or replace)
    # For simplicity in this script, we'll try to load data. 
    # If table doesn't exist, the job config can create it.
    
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE, # Overwrite table
        autodetect=False
    )
    
    # 4. Prepare Data (NDJSON format required for BQ load from file)
    # We read our standard JSON list and convert to NDJSON in memory or temp file
    with open(JSON_FILE, "r") as f:
        data = json.load(f)
        
    # Convert to NDJSON string
    ndjson_data = "\n".join([json.dumps(record) for record in data])
    
    # 5. Load Data
    # We load from a file object (using io.StringIO would work, but let's write a temp file)
    temp_ndjson = "temp_bq_load.json"
    with open(temp_ndjson, "w") as f:
        f.write(ndjson_data)
        
    with open(temp_ndjson, "rb") as source_file:
        job = client.load_table_from_file(
            source_file,
            table_ref,
            job_config=job_config
        )
        
    job.result()  # Waits for the job to complete. 
    
    print(f"Loaded {job.output_rows} rows into {DATASET_ID}.{TABLE_ID}.")
    
    # Cleanup
    if os.path.exists(temp_ndjson):
        os.remove(temp_ndjson)

if __name__ == "__main__":
    upload_to_bigquery()
