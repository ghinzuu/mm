#!/usr/bin/env python

# import sys
import os
import os.path


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
    if not url_to_dl:
        print("No URL to download")
        pass
    if not destination_folder:
        print("No valid path to download the music to")
        pass
    if 'youtube' in url_to_dl:
        youtube_dl_to_mp3(url_to_dl, destination_folder)
    else:
        youget_dl_to_mp3(url_to_dl, destination_folder)


def youtube_dl_to_mp3(url_to_dl, destination_folder):
    only_audio = "--extract-audio --audio-format mp3 "
    playlist = "--no-playlist "
    command = "yt-dlp " + only_audio + playlist \
        + "--path \"" + destination_folder + "\" \"" + url_to_dl + "\""
    os.system(command)


# Test for sc
def youget_dl_to_mp3(url_to_dl, destination_folder):
    """
        You-Get is supposed to be working for several platform such as YouTube
        and SoundCloud. Upon testing recently the dl of YouTube links is very slow :
        https://github.com/soimort/you-get/pull/2950 thus using yt-dlp instead
    """
    command = "you-get -o \"" + destination_folder + "\" \"" + url_to_dl + "\""
    os.system(command)


"""
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
"""
