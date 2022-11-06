"""
This file contains the paths to credential and GCP utilities used in the
project.
Do not commit this file, since it may contain sensitive information.
You can avoid committing the file using the following Git command:
git update-index --assume-unchanged config/gcp.py
"""

CREDENTIALS_JSON = ''
FIREBASE_RTDB_URL = ''
CLOUD_FUNCTIONS_ROOT = ''

RECEIVER_URL = f"{CLOUD_FUNCTIONS_ROOT}/receive"
