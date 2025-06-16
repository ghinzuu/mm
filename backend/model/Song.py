import os
from datetime import datetime
import base64
import mutagen
from mutagen import File
import mutagen.mp3
from mutagen.mp3 import MP3
import mutagen.mp4
import mutagen.flac
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB
from mutagen.easyid3 import EasyID3

import psutil
import time
import ctypes
import win32con
import win32api
import win32file


class Song:
    def __init__(self, filepath):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)

        # Extract metadata
        self.metadata = File(filepath, easy=True)
        if self.metadata:
            self.title = self.metadata.get('title', [self.filename])[0] or ""
            self.artist = self.metadata.get('artist', [""])[0] or ""
            self.album = self.metadata.get('album', [""])[0] or ""
            self.genre = self.metadata.get('genre', [""])[0] or ""
            self.date = self.metadata.get('date', [""])[0] or ""

        else:
            self.title = self.filename
            self.artist = ""
            self.album = ""
            self.genre = ""
            self.date = ""

        self.duration = int(self.metadata.info.length) if self.metadata.info else 0

        # Cover image extraction
        self.cover = self.extract_cover()

        # Custom attributes
        self.date_added = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.mood = ""  # To be set manually later
        self.play_count = 0

    def extract_cover(self):
        """Extracts cover image from metadata and saves it as a file (if necessary)."""

        # Absolute path for default cover image
        default_cover = os.path.abspath("frontend/img/music.png")

        if not self.metadata:
            return default_cover  # Return default if no metadata

        cover_data = None

        try:
            if isinstance(self.metadata, mutagen.mp3.MP3):
                audio = ID3(self.filepath)  # Load ID3 tags
                for tag in audio.values():
                    if isinstance(tag, APIC):  # Check for album cover
                        cover_data = tag.data
                        break  # Take the first available cover

            elif isinstance(self.metadata, mutagen.mp4.MP4) and 'covr' in self.metadata:
                cover_data = self.metadata['covr'][0] if self.metadata['covr'] else None

            elif isinstance(self.metadata, mutagen.flac.FLAC) and 'METADATA_BLOCK_PICTURE' in self.metadata:
                picture_data = base64.b64decode(self.metadata['METADATA_BLOCK_PICTURE'][0])
                picture = mutagen.flac.Picture(picture_data)
                cover_data = picture.data

        except Exception as e:
            print(f"Error extracting cover: {e}")
            return default_cover  # Return default on error

        if cover_data:
            # Save cover inside "frontend/img/"
            covers_dir = os.path.abspath("frontend/img/")
            os.makedirs(covers_dir, exist_ok=True)  # Ensure directory exists

            # Overwrite the same file every time
            current_cover = os.path.join(covers_dir, "current_cover.jpg")

            # Save the new cover image
            with open(current_cover, "wb") as cover_file:
                cover_file.write(cover_data)

            return current_cover  # Return path of extracted cover

        return default_cover  # Return default if no cover was found

    def save_metadata(self, new_metadata):
        """Update and save metadata in the audio file safely."""

        # Release the file lock without killing the app
        if not self.release_file_lock():
            print(f"Could not release the lock on {self.filepath}. Trying again in 1s...")
            time.sleep(1)

        metadata_to_overwrite = File(self.filepath, easy=True)  # Reload file to get a new reference
        if metadata_to_overwrite is None:
            print(f"Error: Could not read metadata for {self.filepath}")
            return

        for key, value in new_metadata.items():
            try:
                metadata_to_overwrite[key] = value
            except KeyError:
                print(f"'{key}' is not a valid EasyID3 field and was skipped.")

        try:
            metadata_to_overwrite.save()
            print("Metadata saved successfully!")
        except Exception as e:
            print("Error saving metadata:", e)

    def release_file_lock(self):
        """Attempts to release file locks without killing the process."""
        handle = None
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                for item in proc.open_files():
                    if item.path == self.filepath:
                        print(f" Trying to release lock from: {proc.name()} (PID: {proc.pid})")

                        # Get a handle to the process
                        handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, proc.pid)
                        if handle:
                            print(f"✅ File lock released from: {proc.name()} (PID: {proc.pid})")
                            win32file.CloseHandle(handle)
                            return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    def force_close_file(self):
        """
        LEGACY - SHOULD BE REMOVED
        Forcefully closes all processes that have locked the file.
        """
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                for item in proc.open_files():
                    if item.path == self.filepath:
                        print(f" Closing file handle in process: {proc.name()} (PID: {proc.pid})")
                        proc.terminate()  # Force terminate the process
                        proc.wait(timeout=3)  # Wait for process to close
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

    def __str__(self):
        return f"{self.title} - {self.artist} ({self.album}, {self.date}) [{self.genre}] | {self.format_time()}"

