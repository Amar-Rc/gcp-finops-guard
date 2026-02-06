import os
import requests
from google.cloud import bigquery
from google.cloud import secretmanager

def access_secret(secret_id):
    client = secretmanager.SecretManagerServiceClient()
    # "Senior" detail: Accessing specific version of secret
    name = f"projects/{os.environ['GCP_PROJECT']}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def check_bigquery_costs(request):
    """Scans BigQuery for queries costing > $1 in the last 24h"""
    client = bigquery.Client()
    
    # Querying the INFORMATION_SCHEMA (The metadata layer)
    query = """
    SELECT user_email, total_bytes_billed, job_id
    FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
    WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    AND total_bytes_billed > 200000000000 -- ~200GB ($1.00)
    ORDER BY total_bytes_billed DESC
    LIMIT 5
    """
    
    query_job = client.query(query)
    results = [row for row in query_job]
    
    if results:
        webhook = access_secret("slack_webhook")
        requests.post(webhook, json={"text": f"High Cost Alert: {results}"})
        return "Alert Sent"
    
    return "All Good"
