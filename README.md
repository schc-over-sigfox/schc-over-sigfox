# SCHC-over-Sigfox

This branch contains an implementation of the receiver side of  [SCHC/Sigfox](https://datatracker.ietf.org/doc/html/draft-ietf-lpwan-schc-over-sigfox).
It is deployable over Google Cloud Functions and uses Firebase Realtime Database as a storage.

## Instructions

The structure is the same as the one in the main branch. The following steps need to be
completed in order to deploy the receiving HTTP function into Google Cloud Functions.

### Set up
1. A Google Cloud Platform account and project are needed.
2. Enable the Cloud Build and Cloud Functions APIs.
3. [Create a Service Account](https://developers.google.com/workspace/guides/create-credentials#create_a_service_account) and [obtain its JSON credential](https://developers.google.com/workspace/guides/create-credentials#create_credentials_for_a_service_account).
4. Save the JSON credentials. As an example, the JSON credentials named `my_credentials.json` is saved inside a directory named `credentials`.
5. Copy the path to your credentials (`credentials/my_credentials.json`) into the variable `CREDENTIALS_JSON` in `config/gcp.py`.

### Using Firebase Realtime Database
1. With the same Google account used for the creation of the GCP project, create a project in [Firebase](https://console.firebase.google.com/).
2. Enable [Firebase Realtime Database](https://firebase.google.com/docs/database) for your project.
3. In the Realtime Database **Rules** dashboard, configure the Rules to allow read and write operations as public.
4. In the Realtime Database **Data** dashboard, copy the reference URL of the database (something like `https://projectname-default-rtdb.firebaseio-com`) into the variable `FIREBASE_RTDB_URL` in `config/gcp.py`.

### Using Cloud Functions
1. In the [Cloud Functions](https://console.cloud.google.com/functions/) dashboard, click on "Create a function".
2. Copy the base URL shown under the **Trigger** section (something like `https://region-projectname.cloudfunctions.net`) into the variable `CLOUD_FUNCTIONS_ROOT` in `config/gcp.py`.

The script `config/gcp.py` should look something like this:
```python
CREDENTIALS_JSON = 'credentials/my_credentials.json'
FIREBASE_RTDB_URL = 'https://projectname-default-rtdb.firebaseio-com'
CLOUD_FUNCTIONS_ROOT = 'https://region-projectname.cloudfunctions.net'

RECEIVER_URL = f"{CLOUD_FUNCTIONS_ROOT}/receive"
```

### Deploying

1. [Install and initialize the Google Cloud CLI](https://cloud.google.com/sdk/docs/initializing).
2. Execute the script `deploy.py`. Change the variable `region` if needed.

## Known issues:

(Inherited from the main branch)

## Authors

* **Sergio Aguilar**: Profile coauthor, developer
* **Sandra Céspedes**: Profile coauthor, advisor
* **Carles Gomez**: Profile coauthor, advisor
* **Rafael Vidal**: Advisor
* **Antonis Platis**: Developer
* **Diego Wistuba**: Profile coauthor, developer
* **Juan Carlos Zúñiga**: Profile coauthor, advisor

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file
for details.