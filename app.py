import streamlit as st
import google.cloud
from google.cloud import firestore
from google.cloud.firestore import Client
from google.oauth2 import service_account
import json
from streamlit_mermaid import st_mermaid
from datetime import timedelta

# -----------------------
# Konfigurace / přihlášení
# -----------------------
st.set_page_config(page_title="Composable CDP", page_icon="🧩", layout="wide")

# Authenticate to Firestore with the JSON account key.
key_dict = json.loads(st.secrets["textkey"])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds, project="gtm-5v5drk2p-mzg3y")

# -----------------------
# Pomocné funkce (UI + transformace)
# -----------------------
NOT_SYNCED = "not synchronised yet"

def humanize_ms(value):
    """Převod milisekund na h:m:s. Vrací NOT_SYNCED pro None/nesmysly."""
    try:
        ms = int(value)
        return str(timedelta(milliseconds=ms))
    except Exception:
        return NOT_SYNCED

def to_int(value):
    """Bezpečný převod na int, jinak NOT_SYNCED."""
    try:
        return int(value)
    except Exception:
        return NOT_SYNCED

def normalize_record(doc_id, doc_dict):
    """
    Vrátí „znormalizovaný“ dict:
    - Pole, která mohou chybět: engagement_time_millis, engaged_sessions, leads_count
      → doplnit NOT_SYNCED
    - Povinná pole dle zadání: email, client_id_collection, last_client_id
    """
    data = doc_dict or {}

    # Povinné údaje — pokud by náhodou nebyly, zobrazíme NOT_SYNCED (ale dle zadání vždy jsou)
    email = data.get("email") or doc_id or NOT_SYNCED
    client_ids_raw = data.get("client_id_collection") or NOT_SYNCED
    last_client_id = data.get("last_client_id") or NOT_SYNCED

    # Volitelná pole
    engagement_time = humanize_ms(data.get("engagement_time_millis"))
    engaged_sessions = to_int(data.get("engaged_sessions"))
    leads_count = to_int(data.get("leads_count"))

    # Zpracování client_id_collection do listu (deduplikace, zachování pořadí)
    client_id_list = []
    if isinstance(client_ids_raw, str) and client_ids_raw != NOT_SYNCED:
        seen = set()
        for part in [p.strip() for p in client_ids_raw.split(",") if p.strip()]:
            if part not in seen:
                seen.add(part)
                client_id_list.append(part)

    return {
        "email": email,
        "client_id_collection_raw": client_ids_raw,
        "client_id_list": client_id_list,
        "last_client_id": last_client_id,
        "engagement_time_hms": engagement_time,
        "engaged_sessions": engaged_sessions,
        "leads_count": leads_count,
        "raw": data
    }

def badge(text):
    return f"<span style='display:inline-block;padding:2px 8px;border-radius:999px;border:1px solid rgba(0,0,0,0.1);background:#f6f8fa;font-size:12px;'>{text}</span>"

def render_profile(n):
    st.markdown("### 📇 Unified user profile")

    # Horní řádek s metrikami
    m1, m2, m3, m4 = st.columns([2,1,1,1])
    with m1:
        st.markdown("**Email**")
        st.code(n["email"], language="text")
        # Client ID summary
        if n["client_id_list"]:
            st.markdown(
                badge(f"{len(n['client_id_list'])} client IDs") + " " +
                badge(f"last: {n['last_client_id']}")
                , unsafe_allow_html=True
            )
        else:
            st.markdown(badge("client IDs: " + (NOT_SYNCED if n["client_id_collection_raw"] == NOT_SYNCED else "0")), unsafe_allow_html=True)

    with m2:
        st.metric("Engaged sessions", value=n["engaged_sessions"])
    with m3:
        st.metric("Leads count", value=n["leads_count"])
    with m4:
        st.metric("Engagement time (h:m:s)", value=n["engagement_time_hms"])

    st.divider()

    # Client IDs detail
    st.markdown("#### Client IDs")
    if n["client_id_list"]:
        # Tabulka s označením last_client_id
        tab_rows = []
        for idx, cid in enumerate(n["client_id_list"], start=1):
            is_last = "✅" if cid == n["last_client_id"] else ""
            tab_rows.append({"#": idx, "client_id": cid, "is_last": is_last})
        st.dataframe(tab_rows, use_container_width=True, hide_index=True)
    else:
        st.info("Client ID collection: **not synchronised yet**")

    # Akce a raw JSON
    c1, c2 = st.columns([1,1])
    with c1:
        if n["raw"]:
            st.download_button(
                label="⬇️ Download raw JSON",
                data=json.dumps(n["raw"], indent=2),
                file_name=f"user_{n['email']}.json",
                mime="application/json"
            )
    with c2:
        with st.expander("Raw JSON (API response)"):
            if n["raw"]:
                st.json(n["raw"])
            else:
                st.write(NOT_SYNCED)

# -----------------------
# UI – hlavička a vyhledávání
# -----------------------
header = st.title("Composable CDP")
st.text("This site is POC user interface of CDP. How to use it?")
st.markdown("1) Submit your (fake) email on [jiriklimecky.tech](https://jiriklimecky.tech/)")
st.markdown("2) You can check data regarding your fake email via search bar below. Note that for GA4 data we need to wait till next export to BigQuery.")

with st.container():
    email_col, button_col = st.columns([3,1])
    with email_col:
        user_email = st.text_input("User email (try e.g. test@test.com):", key="email_input")
    with button_col:
        search = st.button("🔎 Search", use_container_width=True)

# Vyhledání a zobrazení
if user_email and search:
    doc_ref = db.collection("hephaestus_test").document(user_email.strip())
    doc = doc_ref.get()

    if not doc.exists:
        st.warning("No record found for this email.")
    else:
        normalized = normalize_record(doc.id, doc.to_dict())
        render_profile(normalized)

# -----------------------
# Diagramy (ponecháno)
# -----------------------
def display_sequence_diagram():
    sequence_chart = """
    sequenceDiagram
        actor User
        participant WebsiteAndGTM
        participant ServerGTM
        participant GA4
        participant BigQuery
        participant Firestore
        participant Streamlit

        User->>WebsiteAndGTM: Visits website
        WebsiteAndGTM->>ServerGTM: Send pageview/events
        WebsiteAndGTM->>ServerGTM: Send user email
        ServerGTM->>Firestore: Send emails and client_ids
        ServerGTM->>BigQuery: Send emails and client_ids
        ServerGTM->>GA4: Send behavioral data
        GA4->>BigQuery: Export user behavioral data 
        BigQuery->>Firestore: Send transformed behavioral data       
        Streamlit->>Firestore: Query user data
        Streamlit->>Streamlit: Create visualization
        User->>Streamlit: View unified user profile
    """
    st_mermaid(sequence_chart)

def display_component_diagram():
    component_chart = """
    graph TD
        %% Title at the top
        title[Customer Data Platform PoC]
        style title fill:none,stroke:none
        
        %% Web Layer
        subgraph Web Layer
            website["WebsiteAndGTM<br/>Collects user interactions"]
        end
        
        %% Processing Layer
        subgraph Processing Layer
            gtm["Server GTM<br/>Captures user email and GA4 client_id"]
            ga4["GA4<br/>(Analytics)<br/>Tracks user behavior"]
            firestore[(Firestore<br/>NoSQL DB<br/>Stores user identities)]
            bigquery[(BigQuery<br/>Data Warehouse<br/>Stores behavioral data)]
        end
        
        %% Visualization Layer
        subgraph Visualization Layer
            streamlit["Streamlit App<br/>(Python)<br/>Visualizes unified data"]
        end
        
        %% Relationships with specific labels
        website -->|"Sends events/user email"| gtm
        gtm -->|"Emails and client_ids"| firestore
        gtm -->|"Behavioral data"| ga4
        gtm -->|"Emails and client_ids"| bigquery
        ga4 -->|"Daily export"| bigquery
        firestore -->|"User data"| streamlit
        bigquery -->|"Transformed data"| firestore
        
        %% Styling
        style Web Layer fill:#f5f5f5,stroke:#333,stroke-width:2px
        style Processing Layer fill:#e6f3ff,stroke:#333,stroke-width:2px
        style Visualization Layer fill:#f5fff5,stroke:#333,stroke-width:2px
        
        %% Component styling
        style website fill:#fff,stroke:#333,stroke-width:2px
        style ga4 fill:#fff,stroke:#333,stroke-width:2px
        style gtm fill:#fff,stroke:#333,stroke-width:2px
        style firestore fill:#fff,stroke:#333,stroke-width:2px
        style bigquery fill:#fff,stroke:#333,stroke-width:2px
        style streamlit fill:#fff,stroke:#333,stroke-width:2px
    """
    st_mermaid(component_chart)

def main():
    st.markdown("---")
    st.title("Application Architecture")
    st.subheader("Component Diagram")
    display_component_diagram()
    st.subheader("Sequence Diagram")
    display_sequence_diagram()

if __name__ == "__main__":
    main()
