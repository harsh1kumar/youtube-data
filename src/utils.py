import os
from google.oauth2 import service_account


def get_service_account_cred():

    service_account_json = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    credentials = service_account.Credentials.from_service_account_file(
        service_account_json,
    )
    return credentials
