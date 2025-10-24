# Repository Guidelines

## Project Structure & Module Organization
- `app.py` hosts the Streamlit interface and Firestore integrations; helper functions for normalising records live alongside UI logic.
- `requirements.txt` lists Python dependencies required for the Streamlit app and Google Cloud clients.
- `cloud function index.js` and `cloud function package.js` define the Node.js import worker that streams BigQuery exports from Cloud Storage into Firestore.
- `workflow.yaml` contains the Google Cloud Workflow orchestrating ETL steps; update it when adding new data movements.
- `docs/` stores operational notes (for example `docs/ci-smoke.txt` documents CI smoke checks). Keep any runbooks or troubleshooting guides here.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate`: create and activate a local virtual environment.
- `pip install -r requirements.txt`: install Python dependencies for the Streamlit dashboard.
- `streamlit run app.py`: launch the UI locally; requires valid secrets in `.streamlit/secrets.toml`.
- `(cd "cloud function" && npm install)`: pull Node.js dependencies before deploying the Cloud Function.
- `gcloud functions deploy loadCloudStorageToFirestore --runtime nodejs18 --trigger-topic=...`: redeploy the ingestion worker (fill in project-specific flags).

## Coding Style & Naming Conventions
- Python: follow PEP 8, use 4-space indentation, snake_case for functions/variables, and keep helper functions pure where possible.
- JavaScript: prefer ESLint default conventions, camelCase identifiers, async/await for asynchronous flows, and log with contextual prefixes.
- Store configuration in `st.secrets` or environment variables; never commit service account JSON files.

## Testing Guidelines
- There is no automated test suite yet; when adding pure helpers (for example transformations in `app.py`), cover them with `pytest` and place tests in `tests/`.
- For Streamlit changes, run `streamlit run app.py` and exercise the UI flows that touch Firestore.
- For Cloud Function updates, run small fixture files through `node cloud function index.js` (using local emulators) before deploying.

## Commit & Pull Request Guidelines
- Recent history uses short, imperative commit messages (e.g., “Update ai-patch-pr.yml”). Mirror that style and group logical changes together.
- Keep branches focused; reference issues in the commit body when relevant.
- Pull requests should explain the business impact, list manual verification (UI run, emulator test), and attach screenshots or logs for data-facing changes.
- Note any schema or workflow updates that require GCP redeploys so reviewers can plan rollouts.

## Security & Configuration Tips
- Depend on Streamlit Cloud secrets for production credentials; locally, create `.streamlit/secrets.toml` with least-privilege service accounts.
- Rotate service account keys regularly and audit Firestore rules when adding new collections or fields.
