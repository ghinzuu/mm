import os
import io
import threading
import traceback
import shutil
import json
from pathlib import Path
from mimetypes import MimeTypes
import httplib2


from google.auth.transport.requests import Request, AuthorizedSession
#from google.auth.transport.httplib2 import AuthorizedHttp
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

import backend.controller.file_system_manager as fsm


class GoogleDriveApi:
    def __init__(self):
        """Initialize Google Drive API client with modern google-auth libraries."""
        self.SCOPES = ['https://www.googleapis.com/auth/drive']
        creds_path = "backend/google_creds/token_credential.json"
        client_secret = "backend/google_creds/client_secret.json"
        self.creds = None
        self.app_dir = os.getcwd()
        self.music_manager_list = None

        # Try loading existing creds
        if os.path.exists(creds_path):
            try:
                self.creds = Credentials.from_authorized_user_file(creds_path, self.SCOPES)
            except Exception as e:
                print(f"[GoogleDriveApi] Failed to load creds: {e}. Resetting.")
                self.creds = None

        # If creds are missing/invalid, refresh or run OAuth flow
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    print(f"[GoogleDriveApi] Refresh failed ({e}), starting new auth flow.")
                    if os.path.exists(creds_path):
                        os.remove(creds_path)
                    flow = InstalledAppFlow.from_client_secrets_file(client_secret, self.SCOPES)
                    self.creds = flow.run_local_server(port=0)
            else:
                flow = InstalledAppFlow.from_client_secrets_file(client_secret, self.SCOPES)
                self.creds = flow.run_local_server(port=0)

            # Save new creds
            with open(creds_path, 'w') as token:
                token.write(self.creds.to_json())

        # Build Drive service
        self.drive_service = build('drive', 'v3', credentials=self.creds)

        # Ensure Drive folders exist
        self.sync_id = self._get_folder_id("sync")
        #self.pc_id = self._get_folder_id("pc", parent=self.sync_id)
        #self.phone_id = self._get_folder_id("phone", parent=self.sync_id)
        self.music_manager_id = self._get_folder_id("music_manager")

    def _build_service(self):
        """Return a fresh Drive service with its own HTTP transport."""
        #authed_session = AuthorizedSession(self.creds)
        return build("drive", "v3", credentials=self.creds, cache_discovery=False)

    def _get_folder_id(self, folder_name, parent=None):
        """Get or create a folder in Drive, return its ID."""
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent:
            query += f" and '{parent}' in parents"
        results = self.drive_service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get("files", [])
        if files:
            return files[0]["id"]

        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent:
            file_metadata["parents"] = [parent]
        folder = self.drive_service.files().create(body=file_metadata, fields="id").execute()
        return folder["id"]

    def download_file(self, parent_id, filename, dest_dir=None):
        """Download a file from Drive into local cache, return its local Path."""
        query = f"name='{filename}' and '{parent_id}' in parents and trashed=false"
        results = self.drive_service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get("files", [])
        if not files:
            print(f"{filename} not found on Google Drive.")
            return None

        file_id = files[0]["id"]
        request = self.drive_service.files().get_media(fileId=file_id)

        # Default download dir (inside app_dir/tmp if not specified)
        
        dest_dir = Path(dest_dir or (Path(self.app_dir)))
        dest_dir.mkdir(parents=True, exist_ok=True)
        local_path = dest_dir / filename
        with open(local_path, "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

        return local_path

    def upload_file(self, parent_id, filename, overwrite=True):
        """
        Upload a file to Google Drive inside the given folder.
        If overwrite=True, update existing file with the same name instead of creating a new one.
        """
        file_path = Path(filename)
        if not file_path.exists():
            print(f"[Drive] File not found: {filename}")
            return None

        if overwrite:
            # Search for existing file with the same name in the folder
            query = f"name='{file_path.name}' and '{parent_id}' in parents and trashed=false"
            results = self.drive_service.files().list(q=query, fields="files(id, name)").execute()
            files = results.get("files", [])
            if files:
                # Update existing file
                file_id = files[0]["id"]
                media = MediaFileUpload(str(file_path), mimetype="application/json", resumable=True)
                updated_file = self.drive_service.files().update(fileId=file_id, media_body=media).execute()
                print(f"[Drive] Updated file {filename} (ID: {updated_file['id']})")
                return updated_file['id']

        # Create new file if not found or overwrite=False
        file_metadata = {"name": file_path.name, "parents": [parent_id]}
        media = MediaFileUpload(str(file_path), mimetype="application/json", resumable=True)
        new_file = self.drive_service.files().create(body=file_metadata, media_body=media).execute()
        print(f"[Drive] Uploaded new file {filename} (ID: {new_file['id']})")
        return new_file['id']
    
    def _purge_folder(self, folder_id, exclude):
        """Delete all files in a Drive folder except excluded ones."""
        results = self.drive_service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="files(id, name)"
        ).execute()
        for f in results.get("files", []):
            if f["name"] not in exclude:
                self.drive_service.files().delete(fileId=f["id"]).execute()

    def _update_global_inventory(self, mode, local_dict, remote_dict):
        """
        Update global_inventory.json in Drive with current local/remote dicts.
        mode: "pc_to_phone" or "phone_to_pc"
        """
        # Figure out which device is local vs remote
        if mode == "pc_to_phone":
            local_device = "pc"
            remote_device = "phone"
        else:  # "phone_to_pc"
            local_device = "phone"
            remote_device = "pc"

        # Download existing inventory (if any)
        inv_path = self.download_file(self.sync_id, "global_inventory.json")
        if inv_path and inv_path.exists():
            with open(inv_path, "r", encoding="utf-8") as f:
                inventory = json.load(f)
        else:
            inventory = {"synced": {}, "pc": {}, "phone": {}}


        # Update both device inventories
        inventory[local_device] = local_dict
        inventory[remote_device] = remote_dict

        # Synced is the union of both
        inventory["synced"] = {**inventory["pc"], **inventory["phone"]}

        # Save and re-upload
        global_inventory_path = Path("global_inventory.json")
        fsm.save_json(global_inventory_path, inventory)
        self.upload_file(self.sync_id, global_inventory_path.name, overwrite=True)

        return inventory

    def sync(self, local_directory, mode="pc_to_phone"):
        """
        1. scan local dir --> stored in local_dict --> file in local.json 
        2. upload local.json to cloud
        3. download remote.json 
        4. download cloud.json from sync
        5. compare local.json with remote.json: put filename that are in local and not in remote in to_upload
        6. compare cloud.json with local.json: put filename that are in cloud and not in local in to_download
        7. update global_inventory.json and upload it to cloud

        mode pc_to_phone:
        local : pc (sync/pc in gdrive) / remote : phone (sync/phone)
        mode phone_to_pc:
        local : phone (sync/phone) / remote : pc (sync/pc)  

        status_callback reference where we are to the user in the sync process
        """

        #if mode == "pc_to_phone":
        local_filename = "pc_inventory.json"
        remote_filename = "phone_inventory.json"
        if mode == "phone_to_pc":
            local_filename = "phone_inventory.json"
            remote_filename = "pc_inventory.json"

        cloud_filename = "cloud_inventory.json"

        # 1. scan local dir
        local_dict = fsm.list_dir_to_dict(local_directory)
        local_json = Path(self.app_dir) / local_filename
        fsm.save_json(local_json, local_dict)

        # 2. upload
        self.upload_file(self.sync_id, local_filename, overwrite=True)

        # 3. download remote.json
        remote_path = self.download_file(self.sync_id, remote_filename)
        remote_dict = fsm.load_json(remote_path) if remote_path else {}

        # 4. download cloud.json
        cloud_path = self.download_file(self.sync_id, cloud_filename)
        cloud_dict = fsm.load_json(cloud_path) if cloud_path else {}

        # 5. compare
        to_upload = [
            fname
            for h, fname in local_dict.items()
            if h not in remote_dict and h not in cloud_dict
        ]
        to_download = [fname for h, fname in cloud_dict.items() if h not in local_dict]

        # 7. update global inventory
        self._update_global_inventory(mode, local_dict, remote_dict)

        return to_upload, to_download

    def upload_mp3(self, mp3_path, 
                   progress_callback=None, 
                   done_callback=None, 
                   title_callback=None):
        """
        Upload an mp3 file to Google Drive into music_manager and update cloud_inventory.json.

        Args:
            mp3_path (str): Path to the mp3 file to upload.
            progress_callback (callable): Called with progress percentage (0-100).
            done_callback (callable): Called when upload finishes (success=True/False).
            title_callback (callable): Called with file title when known.
        """
        def run():
            try:
                mp3_name = os.path.basename(mp3_path)
                mimeType = MimeTypes().guess_type(mp3_name)[0] or "audio/mpeg"

                if title_callback:
                    title_callback(mp3_name)

                file_metadata = {
                    'name': mp3_name,
                    'mimeType': mimeType,
                    'parents': [self.music_manager_id]  # upload into music_manager
                }
                media = MediaFileUpload(mp3_path, mimetype=mimeType, resumable=True)

                thread_drive_service = self._build_service()
                request = thread_drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, name'
                )

                response = None
                while response is None:
                    status, response = request.next_chunk()
                    if status and progress_callback:
                        progress_callback(int(status.progress() * 100))

                # Update cloud.json with md5 → filename
                file_id = response.get('id')
                md5 = fsm.compute_md5(mp3_path)
                cloud_path = Path(self.app_dir) / "cloud_inventory.json"
                cloud_dict = fsm.load_json(cloud_path) if cloud_path.exists() else {}
                cloud_dict[md5] = mp3_name
                fsm.save_json(cloud_path, cloud_dict)

                print(f"Uploaded {mp3_name}, File ID: {file_id}")
                if done_callback:
                    done_callback(True)
                return file_id

            except HttpError as error:
                print(f"An error occurred during upload: {error}")
                if done_callback:
                    done_callback(False)
                return None
            except Exception as e:
                print(f"[ERROR] Upload failed for {mp3_name}: {e}")
                traceback.print_exc()
            
        threading.Thread(target=run, daemon=True).start()

    def _list_mp3s(self, parent_id: str = None, page_size: int = 100) -> dict[str, str]:
        """
        List MP3s in Google Drive, optionally inside a given folder.

        Args:
            parent_id (str, optional): The folder ID to restrict search. Defaults to None.
            page_size (int): Max results per page. Defaults to 100.

        Returns:
            dict[str, str]: Mapping of filename -> file_id. Empty dict if nothing found.
        """
        try:
            query = "mimeType='audio/mpeg' and trashed = false"
            if parent_id:
                query += f" and '{parent_id}' in parents"

            thread_drive_service = self._build_service()
            results = thread_drive_service.files().list(
                pageSize=page_size,
                q=query,
                spaces="drive",
                fields="nextPageToken, files(id, name)"
            ).execute()

            files = results.get("files", [])
            if not files:
                print("No mp3 files found.")
                return {}

            mp3s = {f["name"]: f["id"] for f in files}
            #for name, fid in mp3s.items():
            #    print(f"{name} ({fid})")

            return mp3s

        except HttpError as error:
            print(f"An error occurred: {error}")
            return {}
        
    def download_mp3(self, mp3_name, destination_folder, 
                     progress_callback=None, 
                     done_callback=None, 
                     title_callback=None, 
                     remove_after=True):
        """
        Download an mp3 file from Google Drive into a local folder and update cloud_inventory.json.

        Args:
            mp3 (dict): File metadata with 'id' and 'name'.
            destination_folder (str): Local folder to save into.
            progress_callback (callable): Called with progress percentage (0-100).
            done_callback (callable): Called when download finishes (success=True/False).
            title_callback (callable): Called with file title when known.
            remove_after (bool): If True, removes file from Drive after download.
        """
        def run():
            try:            
                # getting file ids from google drive
                if not self.music_manager_list:
                    self.music_manager_list = self._list_mp3s(self.music_manager_id)

                mp3_id = self.music_manager_list[mp3_name]

                if title_callback:
                    title_callback(mp3_name)
                
                thread_drive_service = self._build_service()
                request = thread_drive_service.files().get_media(fileId=mp3_id)
                file_holder = io.BytesIO()
                downloader = MediaIoBaseDownload(file_holder, request)

                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status and progress_callback:
                        progress_callback(int(status.progress() * 100))

                # Save file locally
                os.makedirs(destination_folder, exist_ok=True)
                local_path = os.path.join(destination_folder, mp3_name)

                with open(local_path, 'wb') as fs_mp3:
                    file_holder.seek(0)
                    shutil.copyfileobj(file_holder, fs_mp3)

                # Remove reference from cloud.json
                md5 = fsm.compute_md5(local_path)
                cloud_path = Path(self.app_dir) / "cloud_inventory.json"
                cloud_dict = fsm.load_json(cloud_path) if cloud_path.exists() else {}
                if md5 in cloud_dict:
                    del cloud_dict[md5]
                    fsm.save_json(cloud_path, cloud_dict)

                # Optionally remove file from Drive
                if remove_after:
                    thread_drive_service.files().delete(fileId=mp3_id).execute()
                    print(f"Removed {mp3_name} from Drive after download.")

                print(f"Downloaded to {local_path}")
                if done_callback:
                    done_callback(True)
                return local_path

            except HttpError as error:
                print(f"An error occurred during download: {error}")
                if done_callback:
                    done_callback(False)
                return None
            except Exception as e:
                print(f"[ERROR] Download failed for {mp3_name}: {e}")
                traceback.print_exc()
            
        threading.Thread(target=run, daemon=True).start()


