import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import pydantic
import json
import argparse
from typing import Optional


def get_gauth_file() -> str:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--gauth-file",
        type=str,
        default="./.gauth.json",
        help="Path to client secrets file",
    )
    args, _ = parser.parse_known_args()
    return args.gauth_file


CLIENTSECRETS_LOCATION = get_gauth_file()

REDIRECT_URI = 'http://localhost:4100/code'
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/meetings.space.created",
    "https://www.googleapis.com/auth/meetings.space.readonly",
]


class AccountInfo(pydantic.BaseModel):

    email: str
    account_type: str
    extra_info: str

    def __init__(self, email: str, account_type: str, extra_info: str = ""):
        super().__init__(email=email, account_type=account_type, extra_info=extra_info)

    def to_description(self):
        return f"""Account for email: {self.email} of type: {self.account_type}. Extra info for: {self.extra_info}"""


def get_accounts_file() -> str:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--accounts-file",
        type=str,
        default="./.accounts.json",
        help="Path to accounts configuration file",
    )
    args, _ = parser.parse_known_args()
    return args.accounts_file


def get_account_info() -> list[AccountInfo]:
    accounts_file = get_accounts_file()
    with open(accounts_file) as f:
        data = json.load(f)
        accounts = data.get("accounts", [])
        return [AccountInfo.model_validate(acc) for acc in accounts]

class GetCredentialsException(Exception):
  """Error raised when an error occurred while retrieving credentials.

  Attributes:
    authorization_url: Authorization URL to redirect the user to in order to
                       request offline access.
  """

  def __init__(self, authorization_url):
    """Construct a GetCredentialsException."""
    self.authorization_url = authorization_url


class CodeExchangeException(GetCredentialsException):
  """Error raised when a code exchange has failed."""


class NoRefreshTokenException(GetCredentialsException):
  """Error raised when no refresh token has been found."""


class NoUserIdException(Exception):
  """Error raised when no user ID could be retrieved."""


def get_credentials_dir() -> str:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--credentials-dir",
        type=str,
        default=".",
        help="Directory to store OAuth2 credentials",
    )
    args, _ = parser.parse_known_args()
    return args.credentials_dir


def _get_credential_filename(user_id: str) -> str:
    creds_dir = get_credentials_dir()
    return os.path.join(creds_dir, f".oauth2.{user_id}.json")


def get_stored_credentials(user_id: str) -> Optional[Credentials]:
    """Get stored credentials for user.
    
    Args:
        user_id: User's email address
    Returns:
        Stored credentials if found, None otherwise
    """
    try:
        cred_file = _get_credential_filename(user_id)
        if not os.path.exists(cred_file):
            return None
            
        with open(cred_file, 'r') as f:
            creds_data = json.load(f)
            
        credentials = Credentials.from_authorized_user_info(creds_data)
        
        # Refresh if expired
        if credentials.expired:
            credentials.refresh(Request())
            store_credentials(credentials, user_id)
            
        return credentials
        
    except Exception as e:
        logging.error(f"Error loading stored credentials: {e}")
        return None
    



def store_credentials(credentials: Credentials, user_id: str):
    """Store credentials to file.
    
    Args:
        credentials: Google OAuth2 credentials
        user_id: User's email address
    """
    cred_file = _get_credential_filename(user_id)
    os.makedirs(os.path.dirname(cred_file), exist_ok=True)
    
    creds_data = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    
    with open(cred_file, 'w') as f:
        json.dump(creds_data, f)


def get_authorization_url(email_address: str, state: str) -> str:
    """Get the Google OAuth2 authorization URL.
    
    Args:
        email_address: User's email address
        state: State parameter for OAuth flow
    Returns:
        Authorization URL to redirect user to
    """
    # Load client secrets from file
    flow = Flow.from_client_secrets_file(
        CLIENTSECRETS_LOCATION,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    
    # Configure offline access and force approval prompt
    flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        login_hint=email_address,
        prompt='consent',
        state=state
    )
    
    return flow.authorization_url()[0]


def get_credentials(authorization_code: str, state: str) -> Credentials:
    """Exchange authorization code for credentials.
    
    Args:
        authorization_code: OAuth2 authorization code
        state: State parameter from auth flow
    Returns:
        Google OAuth2 credentials
    Raises:
        GetCredentialsException: If credentials cannot be obtained
    """
    try:
        # Create flow instance
        flow = Flow.from_client_secrets_file(
            CLIENTSECRETS_LOCATION,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        
        # Exchange auth code for credentials
        flow.fetch_token(code=authorization_code)
        credentials = flow.credentials

        # Get user info to store credentials
        user_info = get_user_info(credentials)
        email = user_info.get('email')
        
        if credentials.refresh_token:
            store_credentials(credentials, email)
            return credentials
            
        # Try to get stored credentials if no refresh token
        stored_creds = get_stored_credentials(email)
        if stored_creds and stored_creds.refresh_token:
            return stored_creds
            
        # No valid credentials found
        raise NoRefreshTokenException(get_authorization_url(email, state))
        
    except Exception as e:
        logging.error(f"Error getting credentials: {e}")
        raise GetCredentialsException(get_authorization_url("", state))


def get_user_info(credentials: Credentials) -> dict:
    """Get Google user info using credentials.
    
    Args:
        credentials: Valid Google OAuth2 credentials
    Returns:
        Dict containing user info
    Raises:
        NoUserIdException: If user ID cannot be retrieved
    """
    try:
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        if user_info and user_info.get('id'):
            return user_info
        raise NoUserIdException()
    except Exception as e:
        logging.error(f"Error getting user info: {e}")
        raise NoUserIdException()


def authorize_credentials(creds_data):
    """
    Authorize credentials, refreshing them if necessary.
    
    Args:
        credentials (Credentials): Google OAuth2 credentials
    
    Returns:
        Credentials: Authorized credentials
    
    Raises:
        NoUserIdException: If credentials are None or invalid
    """
    if creds_data is None:
        logging.error("Credentials are None")
        raise ValueError("Credentials cannot be None")
        
    try:
        credentials = Credentials.from_authorized_user_info(creds_data)
        
        # Refresh if expired
        if credentials.expired:
            credentials.refresh(Request())
            
        return credentials
    except Exception as e:
        logging.error(f"Error authorizing credentials: {e}")
        if "invalid_grant" in str(e):
            logging.error("Refresh token is invalid or expired")
        # Don't raise NoUserIdException here as it's not related to user ID retrieval
        # Instead, pass through the original exception
        raise

