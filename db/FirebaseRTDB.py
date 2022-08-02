import firebase_admin
from firebase_admin import credentials, db

from config import gcp
from db.JSONStorage import JSONStorage

cred = credentials.Certificate(gcp.CREDENTIALS_JSON)
firebase_admin.initialize_app(cred, {"databaseURL": gcp.FIREBASE_RTDB_URL})


class FirebaseRTDB(JSONStorage):
    """Class to encapsulate storage operations in Firebase Realtime
     Database."""

    def __init__(self) -> None:
        self.REF = db.reference()
        super().__init__()

    def load(self):
        if self.ROOT == "":
            obj = self.REF.get()
        else:
            obj = self.REF.child(self.ROOT).get()
        if obj is None:
            return {}
        return obj

    def save(self) -> None:
        obj = self.REF.child(self.ROOT)
        obj.set(self.JSON)
