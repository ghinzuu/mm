#!/usr/bin/env python

# import sys
import os
import os.path
import shutil

"""
    The purpose of this manager is to download the urls it is provided, whether
    they are from youtube, soundcloudm, spotify or deezer.

    Currently downloads list of youtube links
    TODO :
        soundcloud downloads from list of links
        spotify downloads from list of links
        deezer downloads from list of links
        Single download from list of links
"""


def dl_url_to_mp3(url_to_dl, destination_folder):
    """
        you-get -o r'/Users/dewouter/Music' r'https://www.youtube.com/watch?v=YhSQmvMP4vk'
        you-get -o r'/home/lancelot/Music' r'https://www.youtube.com/watch?v=YhSQmvMP4vk'
        you-get -o r'D:\Downloads' -i r'https://www.youtube.com/watch?v=YhSQmvMP4vk'
    """
    if not url_to_dl:
        print("No URL to download")
        pass
    if not destination_folder:
        print("No valid path to download the music to")
        pass
    command = "you-get -o " + destination_folder + " \"" + url_to_dl + "\""
    os.system(command)


def dl_urls_to_mp3(urls_to_dl, destination_folder):
    if len(urls_to_dl) == 0:
        print("No URLS to download")
        pass
    if not destination_folder:
        print("No valid path to download the music to")
        pass
    for url in urls_to_dl:
        command = "you-get -o " + destination_folder + " \"" + url + "\""
        os.system(command)
