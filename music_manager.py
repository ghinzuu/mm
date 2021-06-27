#!/usr/bin/env python

# import sys
import os
import os.path
import platform
import json
import shutil
from mp3_tagger import MP3File, VERSION_1, VERSION_2, VERSION_BOTH

"""
    PREREQUISITES:
        - Python3 (obviously)
        - Pip3
        - you-get (how does it work on windows?)
        - FFmpeg ?
    ROADMAP:
        Get all url for youtube / soundcloud / spotify
        Dl into repos
        Clean files (check for metadata)
        Make playlists?
    TODO:
        - Make an install file
        - Print usage
        - Make paths (bookmarks + dl destination folder) so it works for any users on any OS
        - Make it compatible for all browsers (chrome, firefox, safari, edge, opera)
        - Options (sysargv): bookmarks file / bookmarks folder name / dl destination folder
        - test you-get with YT list and with soundcloud
"""


def get_default_paths():
    """
        Set the defaults paths. Some of these may be overwritten according to user inputs
    """
    home_directory = os.path.expanduser("~")
    os_name = platform.system()  # get on what OS we are running
    paths = {}
    if 'Windows' in os_name:
        paths["bookmarks_path"] = home_directory + r"\AppData\Local\Google\Chrome\User Data\Default\Bookmarks"
        # paths["download_folder"] = r"C:\Users\%username%\Downloads"
        paths["download_folder"] = home_directory + r"\Downloads"
        paths["destination_folder1"] = home_directory + r"\Music"
    # for macOS :
    if 'Darwin' in os_name:
        paths["bookmarks_path"] = home_directory + "/Library/Application Support/Google/Chrome/Default/Bookmarks"
        paths["download_folder"] = home_directory + "/Downloads"
        paths["destination_folder1"] = home_directory + "/Music"
    if 'Linux' in os_name:
        paths["bookmarks_path"] = home_directory + "/.config/google-chrome/Default/Bookmarks"
        paths["download_folder"] = home_directory + "/Downloads"
        paths["destination_folder1"] = home_directory + "/Music"

    return paths


def get_urls(bookmarks_path, bookmark_folder_name):
    """
        Get all urls to be downloaded (youtube and soundcloud)
    """
    with open(bookmarks_path, 'r') as bookmarks:
        bookmarks_dictionary = json.load(bookmarks)
    music_folder = next(
        folder for folder in bookmarks_dictionary['roots']['bookmark_bar']['children'] if folder["name"] == bookmark_folder_name
    )
    urls = []
    for bookmarks_links in music_folder['children']:
        print(bookmarks_links)
        urls.append(bookmarks_links['url'])
    return urls


def dl_urls_to_mp3(music_to_dl_urls, music_to_dl_destination_folder):
    """
        you-get -o /Users/dewouter/Music 'https://www.youtube.com/watch?v=YhSQmvMP4vk'
        you-get -o /home/lancelot/Music 'https://www.youtube.com/watch?v=YhSQmvMP4vk'
        you-get -o D:\Downloads -i "https://www.youtube.com/watch?v=YhSQmvMP4vk"
    """
    for url in music_to_dl_urls:
        command = "you-get -o " + music_to_dl_destination_folder + " \"" + url + "\""
        os.system(command)


def lists_destination_paths(string_of_destination_paths):
    list_of_destination_paths = []
    for destination_path in string_of_destination_paths.split('?'):
        list_of_destination_paths.append(destination_path)
    return list_of_destination_paths


def syncing_files(path_of_dl_files, list_of_paths_destination):
    print("syncing_files")
    for path in list_of_paths_destination:
        print(path)
        for filename in os.listdir(path_of_dl_files):
            print(filename)
            path_source = path_of_dl_files + "/" + filename
            path_destination = path + "/" + filename
            shutil.copyfile(path_source, path_destination)


def tag_mp3(file):
    mp3 = MP3File(file)
    print(mp3.__dict__)
    mp3.set_version(VERSION_BOTH)
    tags = mp3.get_tags()
    print(tags)
    print(tags['ID3TagV1']['song'])
    #print(tags['ID3TagV2']['artist'])
    # e7695a22aa12f5836d918f6d1b146d3f
    for key in tags['ID3TagV1']:
        print(key)
        mp3.key = ""

    mp3.save()


def main():
    """
        User should be able to define :
            - bookmarks_path
            - bookmark_folder_name
            - download_folder
            - list_of_paths_destination
    """
    # script = sys.argv[0]
    # filename = sys.argv[1]

    paths = get_default_paths()
    paths["download_folder"] = r"D:\Downloads"
    # string_of_destination_paths = paths["destination_folder1"]
    # string_of_destination_paths = r"D:\Music\phone music?F:\MEDIA\phone music"
    string_of_destination_paths = r"D:\Music\phone music"
    list_of_destination_paths = lists_destination_paths(string_of_destination_paths)
    # for key, value in paths:
    #     print(key + " " + value)
    # print(paths)
    bookmark_folder_name = "DL"
    music_to_dl_urls = get_urls(paths["bookmarks_path"], bookmark_folder_name)
    # print(music_to_dl_urls)
    dl_urls_to_mp3(music_to_dl_urls, paths["download_folder"])
    syncing_files(paths["download_folder"], list_of_destination_paths)
    # tag_mp3(r"D:\Music\phone music\01 The Lighthouse.mp3")


if __name__ == "__main__":
    main()
