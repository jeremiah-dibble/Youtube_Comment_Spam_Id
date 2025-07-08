from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from flask import session, url_for, redirect, current_app, request
import os
import pathlib

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]


def get_flow():
    client_secrets = current_app.config['YOUTUBE_CLIENT_SECRETS']
    flow = Flow.from_client_secrets_file(
        client_secrets,
        scopes=SCOPES,
        redirect_uri=url_for('routes.oauth2callback', _external=True)
    )
    return flow


def get_youtube_service():
    if 'credentials' not in session:
        return None
    from google.oauth2.credentials import Credentials
    creds = Credentials(**session['credentials'])
    return build(
        current_app.config['YOUTUBE_API_SERVICE_NAME'],
        current_app.config['YOUTUBE_API_VERSION'],
        credentials=creds
    )
