import streamlit as st
from google.cloud import firestore
import json

# Authenticate to Firestore with the JSON account key.
key_dict = json.loads(st.secrets["textkey"])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds, project="ga4cdp")

#  tady to zkusim vložit
# Streamlit widgets to let a user create a new post
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

