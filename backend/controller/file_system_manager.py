#!/usr/bin/env python

from __future__ import print_function
# import sys
import os
import os.path
import hashlib
from pathlib import Path
import platform
import json
import shutil
import sqlite3
from glob import glob
from mp3_tagger import MP3File, VERSION_BOTH  # , VERSION_1, VERSION_2

"""
    The purposes of this manager are :
        - To know the locations of the music links to be downloaded
            * chrome
            * brave
            * firefox
            * edge
            * safari
        - To know the destinations of the music files when downloaded/uploaded :
            * File system (Windows, MacOS, Linux)
            * Cloud (google drive)
            * Phone (android, iOS)
        - Write to destinations (if not already owned)
"""

CONFIG_FILE = "config.json"
VALID_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a"}

def compute_md5(file_path, chunk_size=8192):
    """Compute MD5 hash of a file."""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def sanitize_path(path: str) -> str:
    """Sanitize path for list filename (e.g., /music/folder -> music_folder)."""
    return path.replace(os.sep, "_").replace("/", "_")

def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: Path, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def list_dir_to_dict(directory: str) -> dict:
    """Scan local folder and build dict {md5:filename}."""
    result = {}
    for file in os.listdir(directory):
        full_path = os.path.join(directory, file)
        if os.path.isfile(full_path) and Path(file).suffix in VALID_EXTENSIONS:
            result[compute_md5(full_path)] = file
    return result

def load_config(parameter):
    if not os.path.exists(CONFIG_FILE):
        save_config("", "")  # Create file if it doesn't exist

    with open(CONFIG_FILE, "r") as file:
        try:
            config = json.load(file)
            return config.get(parameter, "")
        except json.JSONDecodeError:
            return ""
        
def save_config(parameter, value):
    # Load existing config if file exists
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            try:
                config = json.load(file)
            except json.JSONDecodeError:
                config = {}
    else:
        config = {}

    config[parameter] = value

    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)


def get_default_urls_paths():
    """
    Returns default paths for Chrome, Brave, Edge, and Firefox bookmarks
    and default download/music folders based on OS.
    """
    home = os.path.expanduser("~")
    os_name = platform.system()
    paths = {}

    if os_name == 'Windows':
        paths.update({
            "chrome_bookmarks": os.path.join(home, "AppData", "Local", "Google", "Chrome", "User Data", "Default", "Bookmarks"),
            "brave_bookmarks": os.path.join(home, "AppData", "Local", "BraveSoftware", "Brave-Browser", "User Data", "Default", "Bookmarks"),
            "edge_bookmarks": os.path.join(home, "AppData", "Local", "Microsoft", "Edge", "User Data", "Default", "Bookmarks"),
            "firefox_profile_folder": os.path.join(home, "AppData", "Roaming", "Mozilla", "Firefox", "Profiles"),  # contains *.default*/places.sqlite
            "download_folder": os.path.join(home, "Downloads"),
            "music_folder": os.path.join(home, "Music")
        })

    elif os_name == 'Darwin':  # macOS
        paths.update({
            "chrome_bookmarks": os.path.join(home, "Library", "Application Support", "Google", "Chrome", "Default", "Bookmarks"),
            "brave_bookmarks": os.path.join(home, "Library", "Application Support", "BraveSoftware", "Brave-Browser", "Default", "Bookmarks"),
            "edge_bookmarks": os.path.join(home, "Library", "Application Support", "Microsoft Edge", "Default", "Bookmarks"),
            "firefox_profile_folder": os.path.join(home, "Library", "Application Support", "Firefox", "Profiles"),
            "download_folder": os.path.join(home, "Downloads"),
            "music_folder": os.path.join(home, "Music")
        })

    elif os_name == 'Linux':
        paths.update({
            "chrome_bookmarks": os.path.join(home, ".config", "google-chrome", "Default", "Bookmarks"),
            "brave_bookmarks": os.path.join(home, ".config", "BraveSoftware", "Brave-Browser", "Default", "Bookmarks"),
            "edge_bookmarks": os.path.join(home, ".config", "microsoft-edge", "Default", "Bookmarks"),
            "firefox_profile_folder": os.path.join(home, ".mozilla", "firefox"),  # contains *.default*/places.sqlite
            "download_folder": os.path.join(home, "Downloads"),
            "music_folder": os.path.join(home, "Music")
        })

    return paths


def get_urls(bookmarks_path_or_profile, bookmark_folder_name, browser="chrome"):
    """
    Get all URLs from a specific bookmark folder.
    browser: 'chrome', 'brave', 'edge' -> JSON file
             'firefox' -> profile folder with places.sqlite
    Returns a tuple: (list of urls, dict mapping url -> name)
    """
    urls = []
    urls_names = {}

    if browser.lower() == "firefox":
        # Find places.sqlite in profile folder
        sqlite_files = glob(os.path.join(bookmarks_path_or_profile, "*.default*", "places.sqlite"))
        if not sqlite_files:
            raise FileNotFoundError("Firefox places.sqlite not found in profile folder.")
        db_path = sqlite_files[0]

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            # Find the folder ID
            cursor.execute("SELECT id FROM moz_bookmarks WHERE title=? AND type=2", (bookmark_folder_name,))
            folder_row = cursor.fetchone()
            if not folder_row:
                raise ValueError(f"Bookmark folder '{bookmark_folder_name}' not found in Firefox.")
            folder_id = folder_row[0]

            # Get all bookmarks in that folder
            cursor.execute("""
                SELECT p.url, b.title
                FROM moz_bookmarks b
                JOIN moz_places p ON b.fk = p.id
                WHERE b.parent=?
            """, (folder_id,))
            for url, title in cursor.fetchall():
                urls.append(url)
                urls_names[url] = title if title else "Unknown"
        finally:
            conn.close()

    else:
        # JSON-based browsers: Chrome, Brave, Edge
        if not os.path.exists(bookmarks_path_or_profile):
            raise FileNotFoundError(f"Bookmarks file not found: {bookmarks_path_or_profile}")

        with open(bookmarks_path_or_profile, 'r', errors='ignore') as f:
            bookmarks_dict = json.load(f)

        # Find the folder by name
        music_folder = None
        for folder in bookmarks_dict.get('roots', {}).get('bookmark_bar', {}).get('children', []):
            if folder.get("name") == bookmark_folder_name:
                music_folder = folder
                break
        if music_folder is None:
            raise ValueError(f"Bookmark folder '{bookmark_folder_name}' not found.")

        for item in music_folder.get('children', []):
            if 'url' in item:
                urls.append(item['url'])
                urls_names[item['url']] = item.get('name', 'Unknown')

    return urls, urls_names


# legacy
def lists_destination_paths(string_of_destination_paths):
    list_of_destination_paths = []
    for destination_path in string_of_destination_paths.split('?'):
        list_of_destination_paths.append(destination_path)
    return list_of_destination_paths


def copy(source, destination):
    shutil.copy2(Path(source), Path(destination))


def syncing_files(path_of_dl_files, list_of_paths_destination):
    print("syncing_files")
    for path in list_of_paths_destination:
        print(path)
        for filename in os.listdir(path_of_dl_files):
            print(filename)
            path_source = path_of_dl_files + "/" + filename
            path_destination = path + "/" + filename
            shutil.copy2(path_source, path_destination)


def isAValidPath(path):
    if os.path.exists(path):
        return True
    return False

# legacy
def save_destination_folders(destinationPaths):
    destinationPathsFile = open("backend/destinationPaths.txt", "w")
    destinationPathsFile.write(destinationPaths)
    destinationPathsFile.close()

# legacy
def get_saved_destination_folders():
    if os.path.exists("backend/destinationPaths.txt"):
        destinationPathsFile = open("backend/destinationPaths.txt", "r")
        destinationPaths = destinationPathsFile.read()
        destinationPathsFile.close()
        return destinationPaths
    else:
        return os.path.expanduser("~") + r"\Music"

# legacy
def tag_mp3(file):
    mp3 = MP3File(file)
    print(mp3.__dict__)
    mp3.set_version(VERSION_BOTH)
    tags = mp3.get_tags()
    print(tags)
    print(tags['ID3TagV1']['song'])
    # print(tags['ID3TagV2']['artist'])
    # e7695a22aa12f5836d918f6d1b146d3f
    for key in tags['ID3TagV1']:
        print(key)
        mp3.key = ""
    mp3.save()
