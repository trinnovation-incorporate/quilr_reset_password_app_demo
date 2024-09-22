import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


from sqlalchemy.orm import Session
from ..models import OAuthToken  # Adjust the import based on your project structure


def get_access_token_by_user(session: Session, user_id: int):
    """
    Fetch the access token for a specific user.

    :param session: SQLAlchemy session object
    :param user_id: ID of the user
    :return: Access token or None if not found
    """
    oauth_token = session.query(OAuthToken).filter(OAuthToken.user_id == user_id).order_by(OAuthToken.id.desc()).first()
    return oauth_token.access_token if oauth_token else None


def fetch_gmail_messages(access_token):
    try:
        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)
        results = service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])

        if not labels:
            print("No labels found.")
            return
        print("Labels:")
        for label in labels:
            print(label["name"])

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")
