import os
import firebase_admin
from firebase_admin import credentials, db

_app = None

def init_firebase():
    global _app
    if _app is not None:
        return _app

    sa_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "serviceAccountKey.json")
    db_url = os.getenv("FIREBASE_DB_URL")

    if not db_url:
        raise RuntimeError("FIREBASE_DB_URL environment variable not set")

    cred = credentials.Certificate(sa_path)
    _app = firebase_admin.initialize_app(cred, {"databaseURL": db_url})
    return _app

def rtdb_ref(path: str):
    if not path.startswith("/"):
        path = "/" + path
    return db.reference(path)
