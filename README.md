# ppt_alerts-master

Demo alerting/reporting pipeline that assembles PowerPoint slides from anomaly detection results and delivers them via Slack/Teams. Secrets are injected at runtime; none are stored in the repo.

## Components
- `anomaly_slide.py`: builds slides/images for anomalies.
- `send_ppt.py`: sends messages/files to Slack (via `SLACK_BOT_TOKEN`) or email.
- `bigquery.py`: helper to read source data when running locally.
- Cloud Build configs for dev/prod (`cloudbuild_dev.yaml`, `cloudbuild_prod.yaml`).

## Configure (env vars)
- `SLACK_BOT_TOKEN` – bot token for posting.
- `TEAMS_WEBHOOK_URL` – Teams webhook (optional).
- `GOOGLE_APPLICATION_CREDENTIALS` or `SERVICE_ACCOUNT_FILE` – service account JSON if hitting BigQuery.
- Any dataset/table IDs you reference inside the scripts.

## Run locally
```bash
pip install -r requirements.txt  # if present
export SLACK_BOT_TOKEN=replace_me
export TEAMS_WEBHOOK_URL=replace_me
python anomaly_slide.py
```

## Notes
- Use demo/non-sensitive data when sharing publicly.
- Add retries/error handling before production use.
