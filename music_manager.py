#!/usr/bin/env python

# import os
import sys
# from flask import Flask  # online server
# frontend
from PyQt5 import QtWidgets  # , QtCore, QtGui
from frontend.MusicManagerUI import MusicManagerUI
# from frontend.PathsTestingWidget import PathsTestingWidget
# import file_system_manager as fsm
# import download_manager as dlm
# import upload_manager as ulm


"""
    PREREQUISITES:
        - Python3 (obviously)
        - Pip3
        - you-get (how does it work on windows?)
        - FFmpeg ?
    ROADMAP:
        - Get all url for youtube / soundcloud / spotify
        - Dl into repos
        - Clean files (check for metadata)
        - Make playlists?
    TODO:
        - Make an install file
        - Print usage
        - Make paths (bookmarks + dl destination folder) so it works for any users on any OS
        - Make it compatible for all browsers (chrome, firefox, safari, edge, opera)
        - Options (sysargv): bookmarks file / bookmarks folder name / dl destination folder
        - test you-get with YT list and with soundcloud
        - User should be able to define through config file/UI:
            * bookmarks_path
            * bookmark_folder_name
            * download_folder
            * list_of_paths_destination
        - img are not displayed
        
"""


# app = Flask(__name__)

def main():
    # script = sys.argv[0]
    # filename = sys.argv[1]

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    mm_ui = MusicManagerUI()
    mm_ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
