#!/usr/bin/env python

from __future__ import print_function
# import sys
import os
import os.path
import platform
import json
import shutil
from mp3_tagger import MP3File, VERSION_BOTH  # , VERSION_1, VERSION_2

"""
    The purposes of this manager are :
        - To know the locations of the music links to be downloaded
            * chrome
            * brave
            * firefox
        - To know the destinations of the music files when downloaded, i.e. :
            * File system (Windows, MacOS, Linux)
            * Cloud (google cloud/drive + dropbox)
            * Phone (android, iOS)
        - Write to destinations (if not already owned)
"""


def get_default_urls_paths():
    """
        Set the defaults paths. Some of these may be overwritten according to user inputs
    """
    home_directory = os.path.expanduser("~")
    os_name = platform.system()  # get on what OS we are running
    paths = {}
    if 'Windows' in os_name:
        paths["chrome_bookmarks_path"] = home_directory + r"\AppData\Local\Google\Chrome\User Data\Default\Bookmarks"
        paths["brave_bookmarks_path"] = home_directory + r"\AppData\Local\BraveSoftware\Brave-Browser\User Data\Default\Bookmarks"
        # paths["download_folder"] = r"C:\Users\%username%\Downloads"
        paths["download_folder"] = home_directory + r"\Downloads"
        paths["destination_folder1"] = home_directory + r"\Music"
    # for macOS :
    if 'Darwin' in os_name:
        paths["chrome_bookmarks_path"] = home_directory + "/Library/Application Support/Google/Chrome/Default/Bookmarks"
        paths["download_folder"] = home_directory + "/Downloads"
        paths["destination_folder1"] = home_directory + "/Music"
    if 'Linux' in os_name:
        paths["chrome_bookmarks_path"] = home_directory + "/.config/google-chrome/Default/Bookmarks"
        paths["download_folder"] = home_directory + "/Downloads"
        paths["destination_folder1"] = home_directory + "/Music"

    return paths


def get_urls(bookmarks_path, bookmark_folder_name):
    """
        Get all urls to be downloaded (youtube)
    """
    with open(bookmarks_path, 'r') as bookmarks:
        bookmarks_dictionary = json.load(bookmarks)
    music_folder = next(
        folder for folder
        in bookmarks_dictionary['roots']['bookmark_bar']['children']
        if folder["name"] == bookmark_folder_name
    )

    urls = []
    urlsNames = {}
    for bookmarks_links in music_folder['children']:
        # print(bookmarks_links)
        # print(bookmarks_links['url'])
        urls.append(bookmarks_links['url'])
        urlsNames[bookmarks_links['url']] = bookmarks_links['name']

    return urls, urlsNames


def lists_destination_paths(string_of_destination_paths):
    list_of_destination_paths = []
    for destination_path in string_of_destination_paths.split('?'):
        list_of_destination_paths.append(destination_path)
    return list_of_destination_paths


def copy(source, destination):
    shutil.copy2(source, destination)


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


def save_destination_folders(destinationPaths):
    destinationPathsFile = open("backend/destinationPaths.txt", "w")
    destinationPathsFile.write(destinationPaths)
    destinationPathsFile.close()


def get_saved_destination_folders():
    if os.path.exists("backend/destinationPaths.txt"):
        destinationPathsFile = open("backend/destinationPaths.txt", "r")
        destinationPaths = destinationPathsFile.read()
        destinationPathsFile.close()
        return destinationPaths
    else:
        return os.path.expanduser("~") + r"\Music"


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
