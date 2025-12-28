#!/usr/bin/env python

# import sys
import os
import os.path
import subprocess
import threading
import json


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


def dl_url_to_mp3(url_to_dl, destination_folder, progress_callback=None, done_callback=None, title_callback=None):
    if not url_to_dl:
        print("No URL to download")
        pass
    if not destination_folder:
        print("No valid path to download the music to")
        pass

    if 'youtube' in url_to_dl:
        youtube_dl_to_mp3(url_to_dl, destination_folder,
            progress_callback=progress_callback,
            done_callback=done_callback,
            title_callback=title_callback)
    else:
        youtube_dl_to_mp3(url_to_dl, destination_folder,
            progress_callback=progress_callback,
            done_callback=done_callback,
            title_callback=title_callback)


def youtube_dl_to_mp3(url_to_dl, 
                      destination_folder, 
                      progress_callback=None, 
                      done_callback=None, 
                      title_callback=None):
    """
    Download youtube links into destination folder
    """

    # Ensure destination folder exists
    if not os.path.exists(destination_folder):
        try:
            os.makedirs(destination_folder, exist_ok=True)
            print(f"Created destination folder: {destination_folder}")
        except Exception as e:
            print(f"Failed to create destination folder {destination_folder}: {e}")
            if done_callback:
                done_callback(False)
            return

    options = ["-N", "4"]
    only_audio = ["--extract-audio", "--audio-format", "mp3"]
    playlist = ["--no-playlist"]
    path = ["--paths", destination_folder]
    command = ["yt-dlp"] + options + only_audio + playlist + path + [url_to_dl]


    def run():
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
        )

        for line in process.stdout:
            print(line, end="")  # show in terminal
            # Detect title line
            if "[download] Destination:" in line and title_callback:
                try:
                    # Extract between "Destination:" and last file extension
                    filename = line.split("Destination:")[-1].strip()
                    title = filename.rsplit(".", 1)[0]  # remove extension
                    title_callback(title)
                except Exception as e:
                    print("Title parse error:", e)

            # Detect progress line
            if progress_callback and "[download]" in line and "%" in line:
                try:
                    percent = float(line.split("%")[0].split()[-1])
                    progress_callback(percent)
                except:
                    pass
        
            # Detect errors
            error_detected = False
            if "ERROR" in line or "fragment not found" in line:
               error_detected = True

        process.wait() 
        is_process_successful = (process.returncode == 0 and not error_detected)

        if done_callback:
            done_callback(success=is_process_successful)

    # Run in background thread
    threading.Thread(target=run, daemon=True).start()

def list_youtube_playlist(playlist_url):
    """
    Returns a list of items from a YouTube playlist.
    Each item: {"id": some index [optional], "title": str, "url": str}
    """
    command = [
        "yt-dlp",
        "--flat-playlist",   # only metadata, not download
        "--dump-single-json", 
        playlist_url
    ]

    process = subprocess.run(command, capture_output=True, text=True)
    if process.returncode != 0:
        print("Error fetching playlist:", process.stderr)
        return []

    data = json.loads(process.stdout)
    list = []
    for idx, entry in enumerate(data.get("entries", [])):
        list.append({
            "id": str(idx),
            "title": entry.get("title", f"Track {idx+1}"),
            "url": entry.get("url") 
        })

    return list


# Test for sc
# Legacy
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
