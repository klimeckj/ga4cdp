# PoC Composable CDP built with Google Cloud and Streamlit

Composable customer data platform that combines GA4 telemetry, Firestore, and Streamlit to drive real-time personalisation. The stack ingests consented behavioural data, stitches identities, and exposes an operations console for marketers and data teams.

## Architecture Snapshot
- **Data ingestion**: GA4 exports land in BigQuery and are materialised into per-user payloads.
- **Reverse ETL**: A Pub/Sub-triggered Cloud Workflow drops JSON files in Cloud Storage that feed a Node.js Cloud Function (`cloud function index.js`). The function streams records into Firestore without replacing existing fields.
- **Serving layer**: `app.py` (Streamlit) reads Firestore, normalises customer fields, and visualises engagement metrics and identity stitching status.
- **Automation**: `workflow.yaml` orchestrates data refresh jobs; CI notes live in `docs/ci-smoke.txt`.

## Getting Started
1. Clone the repo and create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Provide Streamlit secrets in `.streamlit/secrets.toml` with a service-account JSON under the `textkey` entry.
3. Launch the dashboard:
   ```bash
   streamlit run app.py
   ```
4. For the Cloud Function worker, install Node dependencies and deploy with gcloud:
   ```bash
   (cd "cloud function" && npm install)
   gcloud functions deploy loadCloudStorageToFirestore --runtime nodejs18 --trigger-topic=YOUR_TOPIC --region=YOUR_REGION
   ```

## Local Development Tips
- Use the Firestore emulator for integration testing; set `FIRESTORE_EMULATOR_HOST` before running Streamlit locally.
- Update `workflow.yaml` alongside any changes to BigQuery export shapes or storage prefixes to keep automation aligned.
- Refer to `AGENTS.md` for contributor guidelines covering coding style, testing expectations, and pull-request hygiene.

## Roadmap & Open Questions
- Automate schema validation and add unit coverage for helper transformations in `app.py`.
- Expand docs with end-to-end diagrams and Dataform workflow examples.
- Evaluate alerting for ingestion failures in the Cloud Function pipeline.




