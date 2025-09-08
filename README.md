# Composable CDP built with Google Cloud and Streamlit
Work is in progress. Current state:
- Data from (https://jiriklimecky.euweb.cz/)(https://jiriklimecky.euweb.cz/) collected in privacy compliant way
- Golden Customer Record stored in Firestore to enable realtime personalisation with server-side GTM
- Custom reverse ETL enriches Firestore record with GA4 data from BigQuery
- Identity stiching : All historical GA4 client IDs available for given user email
- User Interface built in Python with Streamlit https://ga4cdp.streamlit.app/ with codebase in https://github.com/klimeckj/ga4cdp
- Tech stack: GA4, GTM, server-side GTM, Google Cloud Platform (BigQuery, Firestore, Dataform, Cloud Functions, Workflows, Pub/Sub, Storage Bucket), Streamlit



