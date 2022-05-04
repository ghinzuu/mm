#!/usr/bin/env python
from __future__ import print_function
# import sys
import os
import os.path

# for google drive
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# google upload / dl
from apiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools

"""
    The purpose of this manager is to establish the connection to either MEGA
    or the Google Drive of the end user. Once connection is established the script
    may:
        - Make files diff between cloud repository and referenced file repository of current system
        - Upload files
        - Download files

    TODO :
        - Google Drive connection
        - Google Drive files diff
        - Google Drive upload
        - Google Drive download
        - MEGA connection
        - MEGA files diff
        - MEGA upload
        - MEGA download
"""


def getGoogleDriveCredentials2(scope):
    credentials = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        credentials = Credentials.from_authorized_user_file('token.json', scope)
    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', scope)
            credentials = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(credentials.to_json())


def getGoogleDriveCredentials(scope):
    # I should test if these paths will work when I'll have an executable
    store = file.Storage('backend/google_creds/storage.json')
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets('backend/google_creds/client_secret.json', scope)
        credentials = tools.run_flow(flow, store)
    return credentials


def google_drive_list_mp3s():
    scope = ['https://www.googleapis.com/auth/drive']
    credentials = getGoogleDriveCredentials(scope)
    try:
        gDrive = build('drive', 'v3', credentials=credentials)

        # Call the Drive v3 API
        results = gDrive.files().list(
            pageSize=10, fields="nextPageToken, files(id, name)").execute()
        mp3s = results.get('files', [])

        if not mp3s:
            print('No files found.')
            return
        print('Files:')
        for mp3 in mp3s:
            print(u'{0} ({1})'.format(mp3['name'], mp3['id']))
    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')


def google_drive_connection():
    SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('drive', 'v3', credentials=creds)

        # Call the Drive v3 API
        results = service.files().list(
            pageSize=10, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            print('No files found.')
            return
        print('Files:')
        for item in items:
            print(u'{0} ({1})'.format(item['name'], item['id']))
    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')


def google_cloud():
    SCOPES = 'https://www.googleapis.com/auth/drive'
    store = file.Storage('storage.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('backend/google_creds/client_secret.json', SCOPES)
        creds = tools.run_flow(flow, store)
    DRIVE = discovery.build('drive', 'v2', http=creds.authorize(Http()))

    FILES = (
        ('backend/hello.txt', False),
        ('backend/hello.txt', True),
    )

    for filename, convert in FILES:
        metadata = {'title': filename}
        res = DRIVE.files().insert(convert=convert, body=metadata,
                media_body=filename, fields='mimeType,exportLinks').execute()
        if res:
            print('Uploaded "%s" (%s)' % (filename, res['mimeType']))

    if res:
        MIMETYPE = 'application/pdf'
        res, data = DRIVE._http.request(res['exportLinks'][MIMETYPE])
        if data:
            fn = '%s.pdf' % os.path.splitext(filename)[0]
            with open(fn, 'wb') as fh:
                fh.write(data)
            print('Downloaded "%s" (%s)' % (fn, MIMETYPE))


def mega_connection():
    pass
