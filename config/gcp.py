"""
This file contains the paths to credential and GCP utilities used in the
project.
Do not commit this file, since it may contain sensitive information.
You can avoid committing the file using the following Git command:
git update-index --assume-unchanged config/gcp.py
"""

CREDENTIALS_JSON = 'credentials/wyschc-2022-11-7d45c631f8ee.json'
FIREBASE_RTDB_URL = 'https://wyschc-2022-11-default-rtdb.firebaseio.com/'
CLOUD_FUNCTIONS_ROOT = 'https://us-central1-wyschc-2022-11.cloudfunctions.net/'

RECEIVER_URL = f"{CLOUD_FUNCTIONS_ROOT}/receive"
