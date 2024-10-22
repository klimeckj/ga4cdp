import streamlit as st
import google.cloud
from google.cloud import firestore
from google.cloud.firestore import Client
from google.oauth2 import service_account
import json

# Authenticate to Firestore with the JSON account key.
key_dict = json.loads(st.secrets["textkey"])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds, project="gtm-5v5drk2p-mzg3y")

#  tady to zkusim vložit
# Streamlit widgets to let a user create a new post
st.title("Composable CDP built with Google Cloud and Streamlit")
st.subheader("This site is POC user interface of CDP. When you sumbit your (fake) email on https://jiriklimecky.tech/, you can check here that the email is stored together with GA4 Client ID")
user_email = st.text_input("User e-mail:")
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

