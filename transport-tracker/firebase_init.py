import os
import firebase_admin 
from firebase_admin import credentials, db

def init_firebase():
    sa_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "serviceAccountKey.json")
    db_url = os.getenv("FIREBASE_DB_URL", "https://transport-tracker-76409-default-rtdb.asia-southeast1.firebasedatabase.app/")  

    if not firebase_admin._apps:
        cred = credentials.Certificate(sa_path)
        firebase_admin.initialize_app(cred, {"databaseURL": db_url})

def rtdb_ref(path: str):
    return db.reference(path)
