import os
import pickle
from typing import TYPE_CHECKING

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

if TYPE_CHECKING:
    from google.auth.credentials import Credentials
    from googleapiclient.discovery import Resource

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


class GmailAuth:
    def __init__(
        self, client_id: str | None = None, client_secret: str | None = None, token_file: str = "token.pickle"
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_file = token_file
        self.creds = None

    def authenticate(self) -> "Credentials":
        if os.path.exists(self.token_file):
            with open(self.token_file, "rb") as token:
                self.creds = pickle.load(token)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not self.client_id or not self.client_secret:
                    raise ValueError(
                        "Client ID and Client Secret are required for authentication. "
                        "Please provide them when creating the GmailAuth instance."
                    )

                client_config = {
                    "installed": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "redirect_uris": ["http://localhost"],
                    }
                }

                flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                self.creds = flow.run_local_server(port=0)

            with open(self.token_file, "wb") as token:
                pickle.dump(self.creds, token)

        if self.creds is None:
            raise RuntimeError("Failed to authenticate")

        return self.creds

    def get_gmail_service(self) -> "Resource":
        creds = self.authenticate()
        return build("gmail", "v1", credentials=creds)
