#!/usr/bin/env python

# import sys
import os
import json

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


def get_urls(bookmark_folder_name):
    """
        Get all urls to be downloaded (youtube and soundcloud)
    """
    # for macOS :
    # _path = '/Users/dewouter/Library/Application Support/Google/Chrome/Default/Bookmarks'
    # for debian Linux :
    _path = '/home/lancelot/.config/google-chrome/Default/Bookmarks'
    with open(_path, 'r') as bookmarks:
        bookmarks_dictionary = json.load(bookmarks)
    music_folder = next(
        folder for folder in bookmarks_dictionary['roots']['bookmark_bar']['children'] if folder["name"] == bookmark_folder_name
    )
    urls = []
    for links in music_folder['children']:
        urls.append(links['url'])
    return urls


def dl_urls_to_mp3(music_to_dl_urls, music_to_dl_destination_folder):
    """
        you-get -o /Users/dewouter/Music 'https://www.youtube.com/watch?v=YhSQmvMP4vk'
        you-get -o /home/lancelot/Music 'https://www.youtube.com/watch?v=YhSQmvMP4vk'
    """
    for url in music_to_dl_urls:
        command = "you-get -o " + music_to_dl_destination_folder + " '" + url + "'"
        os.system(command)


def main():
    # script = sys.argv[0]
    # filename = sys.argv[1]
    bookmark_folder_name = "music"
    music_to_dl_destination_folder = '/home/lancelot/Music'
    music_to_dl_urls = get_urls(bookmark_folder_name)
    # print(musicToDlYTUrls)
    dl_urls_to_mp3(music_to_dl_urls, music_to_dl_destination_folder)


if __name__ == "__main__":
    main()
