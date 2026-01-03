import os
from google.cloud import bigquery
from google.oauth2 import service_account
from config import in_production


def get_bigquery_client(project_id):
    if in_production:
        client = bigquery.Client(project=project_id)

    else:
        credentials = service_account.Credentials.from_service_account_file(
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS", os.getenv("SERVICE_ACCOUNT_FILE", "service_account.json")), scopes=["https://www.googleapis.com/auth/cloud-platform"],
            # 'firestore_key.json', scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )

        # client = bigquery.Client(credentials=credentials, project='daton-272504')
        client = bigquery.Client(credentials=credentials, project=project_id)

    return client
