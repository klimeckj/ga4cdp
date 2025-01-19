import streamlit as st
import google.cloud
from google.cloud import firestore
from google.cloud.firestore import Client
from google.oauth2 import service_account
import json
from streamlit_mermaid import st_mermaid

# Authenticate to Firestore with the JSON account key.
key_dict = json.loads(st.secrets["textkey"])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds, project="gtm-5v5drk2p-mzg3y")

#  tady to zkusim vložit
# Streamlit widgets to let a user create a new post
header = st.title("Composable CDP built with Google Cloud and Streamlit")
sub_text = st.text("This site is POC user interface of CDP. How to use it?")
sub_text = st.markdown("1. Submit your (fake) email on [jiriklimecky.tech](https://jiriklimecky.tech/)")
sub_text = st.text("2. You can check data regarding your fake email via search bar below. Note that for GA4 data we need to wait till next export to BigQuery.")
user_email = st.text_input("User email:")
search = st.button("Search")

# Once the user has submitted, upload it to the database
if user_email and search:
    doc_ref = db.collection("hephaestus_test").document(user_email)
    doc = doc_ref.get()
    st.write("searched e-mail: ", doc.id)
    st.write("known informations: ", doc.to_dict())

# Create a reference to the Google post.
# doc_ref = db.collection("hephaestus_test").document(user_email)

# Then get the data at that reference.
#doc = doc_ref.get()

# Let's see what we got!
#st.write("searched e-mail: ", doc.id)
#st.write("known informations: ", doc.to_dict())

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
    st.title("Application Architecture")
    st.subheader("Component Diagram")
    display_component_diagram()
    st.subheader("Sequence Diagram")
    display_sequence_diagram()

if __name__ == "__main__":
    main()
