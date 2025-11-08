import streamlit as st
import google.cloud
from google.cloud import firestore
from google.cloud.firestore import Client
from google.oauth2 import service_account
import json
from streamlit_mermaid import st_mermaid
from datetime import timedelta
import smtplib
from email.mime.text import MIMEText

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
SEGMENT_BATCH_LIMIT = 25
VALIDITY_OPTIONS = ["valid", "invalid", "unknown"]

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

def normalize_email_validity(value):
    """
    Vrátí 'valid' | 'invalid' | 'unknown' | NOT_SYNCED podle vstupu.
    Akceptuje bool, i různé stringy (true/false/yes/no/ok/deliverable/bounced/unknown...).
    """
    if value is None:
        return NOT_SYNCED

    if isinstance(value, bool):
        return "valid" if value else "invalid"

    # Pokus o čitelnou klasifikaci stringů / čísel
    try:
        v = str(value).strip().lower()
    except Exception:
        return NOT_SYNCED

    valid_set = {"valid", "true", "yes", "1", "ok", "deliverable", "clean", "good"}
    invalid_set = {"invalid", "false", "no", "0", "undeliverable", "bounced", "bad"}
    unknown_set = {"unknown", "unchecked", "n/a", "na", "null", "none"}

    if v in valid_set:
        return "valid"
    if v in invalid_set:
        return "invalid"
    if v in unknown_set:
        return "unknown"

    # fallback – zobraz co přišlo (ale ať je to hezky malé)
    return v or NOT_SYNCED

def badge(text):
    return f"<span style='display:inline-block;padding:2px 8px;border-radius:999px;border:1px solid rgba(0,0,0,0.1);background:#f6f8fa;font-size:12px;'>{text}</span>"

def validity_badge(validity_value):
    """
    Barevný chip pro email_validity.
    """
    v = validity_value
    color = "#e5e7eb"  # default šedá
    fg = "#111827"

    if v == "valid":
        color = "#dcfce7"  # zelená světlá
        fg = "#065f46"
        label = "Email validity: valid"
    elif v == "invalid":
        color = "#fee2e2"  # červená světlá
        fg = "#7f1d1d"
        label = "Email validity: invalid"
    elif v == "unknown":
        color = "#fef9c3"  # žlutá světlá
        fg = "#713f12"
        label = "Email validity: unknown"
    elif v == NOT_SYNCED:
        color = "#f3f4f6"  # šedá
        fg = "#374151"
        label = f"Email validity: {NOT_SYNCED}"
    else:
        # neznámá hodnota – zobrazíme text
        label = f"Email validity: {v}"

    return f"<span style='display:inline-block;padding:2px 10px;border-radius:999px;border:1px solid rgba(0,0,0,0.08);background:{color};color:{fg};font-size:12px;font-weight:600;'>{label}</span>"

def normalize_record(doc_id, doc_dict):
    """
    Vrátí „znormalizovaný“ dict:
    - Povinná pole dle zadání: email, client_id_collection, last_client_id
    - Volitelná: engagement_time_millis, engaged_sessions, leads_count, email_validity
      → pokud chybí, doplníme NOT_SYNCED
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
    email_validity = normalize_email_validity(data.get("email_validity"))

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
        "email_validity": email_validity,
        "raw": data
    }

def render_profile(n):
    st.markdown("### 📇 Unified user profile")

    # Horní řádek s metrikami
    m1, m2, m3, m4 = st.columns([2,1,1,1])
    with m1:
        st.markdown("**Email**")
        st.code(n["email"], language="text")

        chips = []
        # Client IDs chipy
        if n["client_id_list"]:
            chips.append(badge(f"{len(n['client_id_list'])} client IDs"))
            chips.append(badge(f"last: {n['last_client_id']}"))
        else:
            chips.append(badge("client IDs: " + (NOT_SYNCED if n["client_id_collection_raw"] == NOT_SYNCED else "0")))
        # Email validity chip
        chips.append(validity_badge(n["email_validity"]))

        st.markdown(" ".join(chips), unsafe_allow_html=True)

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

def query_segment(validity_filter, min_sessions, min_leads, limit=SEGMENT_BATCH_LIMIT):
    """
    Stream users from Firestore, normalise them, and return a capped list for the UI.
    """
    statuses = [v for v in validity_filter if v in VALIDITY_OPTIONS]
    rows = []

    try:
        docs = db.collection("hephaestus_test").stream()
    except Exception as exc:
        st.error(f"Unable to query Firestore: {exc}")
        return rows

    for doc in docs:
        normalized = normalize_record(doc.id, doc.to_dict())
        validity = normalized["email_validity"]

        if statuses and validity not in statuses:
            continue

        engaged_value = normalized["engaged_sessions"] if isinstance(normalized["engaged_sessions"], int) else 0
        leads_value = normalized["leads_count"] if isinstance(normalized["leads_count"], int) else 0

        if engaged_value < min_sessions:
            continue
        if leads_value < min_leads:
            continue

        rows.append({
            "email": normalized["email"],
            "email_validity": validity,
            "engaged_sessions": normalized["engaged_sessions"],
            "leads_count": normalized["leads_count"],
            "engagement_time_hms": normalized["engagement_time_hms"],
        })

        if len(rows) >= limit:
            break

    return rows

def _mail_settings():
    """
    Safely pull SMTP configuration from st.secrets['mail'] if available.
    """
    try:
        secrets_section = st.secrets.get("mail", {})
    except Exception:
        try:
            secrets_section = st.secrets["mail"]
        except Exception:
            secrets_section = {}
    try:
        return dict(secrets_section)
    except Exception:
        return secrets_section or {}

def send_email_batch(recipients, subject, body):
    """
    Send emails sequentially via SMTP. Returns (success_emails, error_dicts).
    """
    if not recipients:
        return [], [{"email": None, "error": "No recipients supplied."}]

    mail_conf = _mail_settings()
    required = ["smtp_host", "smtp_port", "username", "password", "from_email"]
    missing = [key for key in required if not mail_conf.get(key)]
    if missing:
        raise ValueError(
            "Mail secrets incomplete. Please add "
            + ", ".join(missing)
            + " under st.secrets['mail']."
        )

    host = mail_conf["smtp_host"]
    port = int(mail_conf.get("smtp_port", 587))
    sender = mail_conf.get("from_email") or mail_conf.get("username")
    sender_name = mail_conf.get("from_name")
    formatted_sender = f"{sender_name} <{sender}>" if sender_name else sender
    use_tls = mail_conf.get("starttls", True)
    timeout = int(mail_conf.get("smtp_timeout", 20))

    successes = []
    errors = []

    try:
        with smtplib.SMTP(host, port, timeout=timeout) as smtp:
            if use_tls:
                smtp.starttls()
            username = mail_conf.get("username")
            password = mail_conf.get("password")
            if username and password:
                smtp.login(username, password)

            for recipient in recipients:
                msg = MIMEText(body, "plain", "utf-8")
                msg["Subject"] = subject
                msg["From"] = formatted_sender
                msg["To"] = recipient

                try:
                    smtp.sendmail(sender, [recipient], msg.as_string())
                    successes.append(recipient)
                    print(f"[email-poc] sent to {recipient}")
                except Exception as exc:
                    errors.append({"email": recipient, "error": str(exc)})
                    print(f"[email-poc] failed for {recipient}: {exc}")
    except Exception as exc:
        raise ValueError(f"Unable to reach SMTP server: {exc}") from exc

    return successes, errors

# -----------------------
# UI – hlavička a vyhledávání
# -----------------------
header = st.title("Composable CDP")
st.text("This site is POC user interface of CDP. How to use it?")
st.markdown("1) Submit your (fake) email on [jiriklimecky.euweb.cz](https://jiriklimecky.euweb.cz/)")
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
# Segmentace a rozesílka emailů (PoC)
# -----------------------
st.divider()
st.subheader("✉️ Email subgroup PoC")

if "segment_preview" not in st.session_state:
    st.session_state["segment_preview"] = []
if "segment_meta" not in st.session_state:
    st.session_state["segment_meta"] = {
        "validity": ["valid"],
        "min_sessions": 0,
        "min_leads": 0,
        "test_email": ""
    }
if "segment_subject" not in st.session_state:
    st.session_state["segment_subject"] = "Composable CDP PoC outreach"
if "segment_body" not in st.session_state:
    st.session_state["segment_body"] = (
        "Hi there,\n\nThanks for trying the Composable CDP PoC. "
        "Let us know what you think!\n\n– The CDP team"
    )

previous_meta = st.session_state["segment_meta"]
default_validity = previous_meta.get("validity") or ["valid"]
default_sessions = int(previous_meta.get("min_sessions", 0))
default_leads = int(previous_meta.get("min_leads", 0))
default_test_email = previous_meta.get("test_email", "")

with st.form("segment_filter_form"):
    col1, col2 = st.columns([2, 1])
    with col1:
        validity_choices = st.multiselect(
            "Email validity filter",
            VALIDITY_OPTIONS,
            default=[v for v in default_validity if v in VALIDITY_OPTIONS] or VALIDITY_OPTIONS,
            help="Only contacts matching these statuses will be included."
        )
    with col2:
        test_email = st.text_input(
            "Optional test email override",
            value=default_test_email,
            help="Provide an address to route the send to a single inbox first."
        )
    min_sessions = st.number_input(
        "Minimum engaged sessions",
        min_value=0,
        value=default_sessions,
        step=1
    )
    min_leads = st.number_input(
        "Minimum leads count",
        min_value=0,
        value=default_leads,
        step=1
    )
    preview_request = st.form_submit_button("Preview subgroup", use_container_width=True)

if preview_request:
    segment_rows = query_segment(validity_choices, int(min_sessions), int(min_leads))
    st.session_state["segment_preview"] = segment_rows
    st.session_state["segment_meta"] = {
        "validity": validity_choices,
        "min_sessions": int(min_sessions),
        "min_leads": int(min_leads),
        "test_email": test_email.strip()
    }
    if not segment_rows:
        st.info("No contacts met the current filters. Try relaxing the thresholds.")

segment_rows = st.session_state.get("segment_preview", [])
segment_meta = st.session_state.get("segment_meta", {})
test_email_override = segment_meta.get("test_email", "").strip()

if segment_rows:
    count_badge = badge(f"{len(segment_rows)} recipients (max {SEGMENT_BATCH_LIMIT})")
    st.markdown(f"**Previewed subgroup** {count_badge}", unsafe_allow_html=True)
    st.dataframe(segment_rows, use_container_width=True, hide_index=True)
    if len(segment_rows) == SEGMENT_BATCH_LIMIT:
        st.caption(f"Showing the first {SEGMENT_BATCH_LIMIT} contacts to keep the UI responsive.")
    if test_email_override:
        st.warning(f"Test mode is ON – send action will target only `{test_email_override}`.")
else:
    st.info("Use the form above to preview a subgroup of contacts for outreach.")

if segment_rows:
    recipients = [row["email"] for row in segment_rows if row.get("email")]
    effective_recipients = [test_email_override] if test_email_override else recipients

    st.markdown("#### Send PoC email")
    subject = st.text_input("Email subject", key="segment_subject")
    body = st.text_area("Email body", key="segment_body", height=180)
    confirm_send = st.checkbox(
        "I confirm these recipients should receive this message.",
        key="segment_confirm"
    )
    success_placeholder = st.empty()
    error_placeholder = st.empty()
    send_clicked = st.button(
        "Send to subgroup",
        disabled=not confirm_send or not effective_recipients,
        type="primary",
        key="segment_send_button"
    )

    if send_clicked and confirm_send:
        try:
            successes, errors = send_email_batch(
                effective_recipients[:SEGMENT_BATCH_LIMIT],
                subject,
                body
            )
            if successes:
                success_placeholder.success(f"Successfully sent {len(successes)} email(s).")
            if errors:
                error_placeholder.error(f"{len(errors)} email(s) failed. See details below.")
                with st.expander("Delivery errors", expanded=False):
                    for err in errors:
                        st.write(f"{err.get('email', 'n/a')}: {err.get('error')}")
        except ValueError as exc:
            error_placeholder.error(str(exc))
else:
    st.caption("Preview a subgroup to unlock the send flow.")

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
