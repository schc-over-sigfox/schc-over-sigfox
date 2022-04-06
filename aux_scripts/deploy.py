import os

os.system("gcloud functions deploy hello_get --region southamerica-east1 --entry-point hello_get --runtime python37 --trigger-http --allow-unauthenticated")
os.system("gcloud functions deploy clean --region southamerica-east1 --entry-point clean --runtime python37 --trigger-http --allow-unauthenticated")
os.system("gcloud functions deploy http_reassemble --region southamerica-east1 --entry-point http_reassemble --runtime python37 --trigger-http --allow-unauthenticated")
os.system("gcloud functions deploy test --region southamerica-east1 --entry-point test --runtime python37 --trigger-http --allow-unauthenticated")
os.system("gcloud functions deploy clean_window --region southamerica-east1 --entry-point clean_window --runtime python37 --trigger-http --allow-unauthenticated")
