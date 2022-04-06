import os

fragdir = "receiver/testing/received"


def upload_blob(text, blob_name):
    with open(f"{fragdir}/{blob_name}", 'w') as f:
        f.write(str(text))


def create_folder(folder_name):
    os.mkdir(f"{fragdir}/{folder_name}")


def read_blob(blob_name):
    with open(f"{fragdir}/{blob_name}", 'r') as f:
        res = f.read()
    return res


def delete_blob(blob_name):
    if os.path.isfile(f"{fragdir}/{blob_name}"):
        os.remove(f"{fragdir}/{blob_name}")
    else:
        pass


def exists_blob(blob_name):
    return os.path.isfile(f"{fragdir}/{blob_name}")


def exists_folder(folder_name):
    return os.path.isdir(f"{fragdir}/{folder_name}")


def size_blob(blob_name):
    return os.path.getsize(f"{fragdir}/{blob_name}")


def blob_list(blob_name=''):
    return os.listdir(f"{fragdir}/{blob_name}")