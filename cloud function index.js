/*
Cloud function which takes JSON from Cloud Storage Bucket and imports it to Firestore based on key. 

Heavily inspired by: https://stacktonic.com/article/how-to-export-big-query-data-to-google-firestore-and-gtm-server

Made changes: 
- keeping "." in data written to firestore
-  change of method for writing to Firestore to not replace whole document if there are already any other data
*/

'use strict';

const admin = require('firebase-admin');
const {Storage} = require('@google-cloud/storage');
const split = require('split');
const { pipeline } = require('stream/promises');


// Upload functioin
async function jsontoFirestore(file, firestoreKey, firestoreCollection) { 
  
   let keysWritten = 0;
  
   return new Promise((resolve, reject) => {
       file.createReadStream()
       .on('error', error => reject(error))
       .on('response', (response) => {
           // connection to GCS opened
       }).pipe(split())
       .on('data',  async record => {
           if (!record || record === "") return;
               keysWritten++;


               const data = JSON.parse(record);
               const key = data[firestoreKey].replace(/[/]/g, '');


               try {
                   await admin.firestore().collection(firestoreCollection).doc(key).set(data, { merge: true })
               } catch(e) {
                   console.log(`Error setting document:  ${e}`);
               }
       })
       .on('end', () => {
           console.log(`Successfully written ${keysWritten} keys to Firestore.`);
       })
       .on('error', error => reject(error));
   });
}   


/**
* Triggered from a Pub/Sub message.
*
* @param {!Object} event Event payload.
* @param {!Object} context Metadata for the event.
*/
exports.loadCloudStorageToFirestore = async(event, context) => {


   const pubSubMessage = event.data ? Buffer.from(event.data, 'base64').toString(): '{}';
   const config = JSON.parse(pubSubMessage);


   console.log(config)


   if (typeof config.projectId != 'undefined') {


       const projectId = config.projectId;
       const bucketName = config.bucketName;
       const bucketPath = config.bucketPath;
       const firestoreCollection = config.firestoreCollection;
       const firestoreKey = config.firestoreKey;


       console.log(`Initiated new import to Firebase: gs://${bucketName}/${bucketPath}`)


       // Init Firebase
       if (admin.apps.length === 0) {
           admin.initializeApp({ projectId: projectId })
       }


       // Init Storage
       const storage = new Storage()
       const bucket = storage.bucket(bucketName);
       const file = bucket.file(bucketPath);


       try {
      
           // TO-DO: Remove old records


           // Read file and send to Firestore
           await jsontoFirestore(file, firestoreKey, firestoreCollection);


      
       } catch(e) {
           console.log(`Error importing ${bucketPath} to Firestore: ${e}`);
       }
   }


};
