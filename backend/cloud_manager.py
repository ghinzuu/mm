#!/usr/bin/env python
from __future__ import print_function
# import sys
import os
import os.path
import io
from mimetypes import MimeTypes
import shutil

# for google drive
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

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


class GoogleDriveApi():

    def __init__(self):
        scope = ['https://www.googleapis.com/auth/drive']
        store = file.Storage('backend/google_creds/storage.json')
        self.credentials = store.get()
        if not self.credentials or self.credentials.invalid:
            flow = client.flow_from_clientsecrets(
                'backend/google_creds/client_secret.json', scope)
            self.credentials = tools.run_flow(flow, store)
        self.drive_service = build('drive', 'v3', credentials=self.credentials)

    # Currently, also provide shared drives, which is unnecessary.
    def list_mp3s(self):
        try:
            results = self.drive_service.files().list(
                pageSize=4, fields="nextPageToken, files(id, name)").execute()
            mp3s = results.get('files', [])

            if not mp3s:
                print('No files found.')
                return
            print('Files: (this is in cloud_manager.py)')
            for mp3 in mp3s:
                print(u'{0} ({1})'.format(mp3['name'], mp3['id']))
            print("There is %d mp3 in the list" % len(mp3s))
            return mp3s

        except HttpError as error:
            # TODO(developer) - Handle errors from drive API.
            print(f'An error occurred: {error}')

    # /!\ Needs to be tested
    def download_mp3(self, mp3, destination_folder):
        request = self.drive_service.files().get_media(fileId=mp3['id'])
        file_holder = io.BytesIO()
        downloader = MediaIoBaseDownload(file_holder, request)
        done = False
        mp3_path = mp3['name']
        mp3_directory = os.path.dirname(mp3_path)
        while done is False:
            status, done = downloader.next_chunk()
            print("Download %s %d%%." % (mp3_path, int(status.progress() * 100)))

        file_holder.seek(0)  # Idk why dis?

        # Write the received data to the file
        # file_path = destination_folder + "/" + mp3['name']
        if not os.path.exists(mp3_directory):
            os.makedirs(mp3_directory)
        with open(mp3_path, 'wb') as fs_mp3:
            shutil.copyfileobj(file_holder, fs_mp3)

    # /!\ Needs to be tested
    def upload_mp3(self, mp3_path):
        mp3_name = mp3_path.split('/')[-1]
        mimeType = MimeTypes().guess_type(mp3_name)[0]
        file_metadata = {
            'name': mp3_name,
            'mimeType': mimeType
        }

        media = MediaFileUpload(mp3_path, mimetype=mimeType, resumable=True)

        uploaded_file = self.drive_service.files().create(body=file_metadata,
                                                          media_body=media,
                                                          fields='id').execute()
        print('File ID: %s' % uploaded_file.get('id'))

    """
    def download_list(self, mp3_list, destination_folder):
        for mp3 in mp3_list:
            request = self.drive_service.files().get_media(fileId=mp3['id'])
            file_holder = io.BytesIO()
            downloader = MediaIoBaseDownload(file_holder, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print("Download %s %d%%." %
                      mp3['name'], int(status.progress() * 100))

            file_holder.seek(0)  # Idk why dis?

            # Write the received data to the file
            file_path = destination_folder + "/" + mp3['name']
            with open(file_path, 'wb') as fs_mp3:
                shutil.copyfileobj(file_holder, fs_mp3)

    def getGoogleDriveCredentials2(scope):
        credentials = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            credentials = Credentials.from_authorized_user_file(
                'token.json', scope)
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
        return credentials

    def getGoogleDriveCredentials(scope):
        # I should test if these paths will work when I'll have an executable
        store = file.Storage('backend/google_creds/storage.json')
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(
                'backend/google_creds/client_secret.json', scope)
            credentials = tools.run_flow(flow, store)
        return credentials

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
            flow = client.flow_from_clientsecrets(
                'backend/google_creds/client_secret.json', SCOPES)
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

        """


class MegaApi():
    pass
