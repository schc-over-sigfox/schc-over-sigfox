import os

region = "us-central1"
runtime = "python39"
function_name = "receive"

os.system(
    f"gcloud functions deploy {function_name} "
    f"--region {region} "
    f"--allow-unauthenticated "
    f"--entry-point {function_name} "
    f"--runtime {runtime} "
    f"--trigger-http "
    f"--security-level secure-always"
)
