from time import perf_counter

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from config import config


class Database(object):
    ref = None
    name = None

    def __init__(self, bucket_name):
        print('init db + {}'.format(bucket_name))
        # Fetch the service account key JSON file contents

        cred = credentials.Certificate(config.CREDENTIALS_FILE_FIREBASE)

        # Initialize the app with a service account, granting admin privileges
        firebase_admin.initialize_app(cred, {'databaseURL': config.FIREBASE_RTDB_URL})

        # Get a database reference to our database.
        self.ref = db.reference()
        self.name = bucket_name

    def save(self, blob_text, destination_blob_name):
        print("[DATABASE]: saving in {}".format(self.name + "/" + destination_blob_name))
        data_ref = self.ref.child(self.name + "/" + destination_blob_name)
        data_ref.set(blob_text)

    def read(self, blob_name):
        print("[DATABASE]: reading from {}".format(self.name + "/" + blob_name))
        data_ref = self.ref.child(self.name + "/" + blob_name)
        return data_ref.get()

    def delete(self, blob_name):
        print("[DATABASE]: deleting from {}".format(self.name + "/" + blob_name))
        data_ref = self.ref.child(self.name + "/" + blob_name)
        return data_ref.delete()

    def delete_all(self):
        print("[DATABASE]: deleting from {}".format(self.name))
        data_ref = self.ref.child(self.name)
        return data_ref.delete()


# Init database with the bucket name
database = Database(config.BUCKET_NAME)


def upload_blob(blob_text, destination_blob_name):
    global database
    # t_i = perf_counter()
    database.save(blob_text, destination_blob_name)
    # t_f = perf_counter()
    # print(f"Upload took {t_f - t_i} seconds")


def create_folder(folder_name):
    global database
    # t_i = perf_counter()
    database.save("", folder_name)
    # t_f = perf_counter()
    # print(f"Folder creation took {t_f - t_i} seconds")


def read_blob(blob_name):
    global database
    # t_i = perf_counter()
    res = database.read(blob_name)
    # t_f = perf_counter()
    # print(f"Read took {t_f - t_i} seconds")
    return res


def delete_blob(blob_name):
    global database
    # t_i = perf_counter()
    database.delete(blob_name)
    # t_f = perf_counter()
    # print(f"Deletion took {t_f - t_i} seconds")


def delete_all():
    global database
    database.delete_all()


def exists_blob(blob_name):
    return read_blob(blob_name) is not None


def size_blob(blob_name):
    return len(str(read_blob(blob_name)))


def blob_list(blob_name=''):
    root = read_blob(blob_name)
    # Try to redefine without isinstance
    if isinstance(root, dict):
        return list(read_blob(blob_name).keys())
