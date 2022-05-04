#!/usr/bin/env python

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QApplication
import os
import time
import backend.file_system_manager as fsm
import backend.download_manager as dlm


"""
    This manager displays all the URLS to be downloaded,
    based on the inputs provided by the user on the MusicManagerUI.
"""


class CloudUI(object):
    def setupUi(self, downloadUI, urls_list, destination_paths):
        downloadUI.setObjectName("downloadUI")
        downloadUI.resize(393, 235)
        downloadUI.setWindowTitle("Download")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("frontend/img/mmIcon2.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        downloadUI.setWindowIcon(icon)

        self.state_label = QtWidgets.QLabel(downloadUI)
        self.state_label.setGeometry(QtCore.QRect(30, 20, 321, 16))
        self.state_label.setObjectName("state_label")

        self.action_label = QtWidgets.QLabel(downloadUI)
        self.action_label.setGeometry(QtCore.QRect(30, 50, 321, 16))
        self.action_label.setObjectName("action_label")

        self.progression_label = QtWidgets.QLabel(downloadUI)
        self.progression_label.setGeometry(QtCore.QRect(310, 90, 41, 16))
        self.progression_label.setObjectName("progression_label")

        self.progressBar = QtWidgets.QProgressBar(downloadUI)
        self.progressBar.setGeometry(QtCore.QRect(30, 90, 261, 23))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")

        self.action_labelImg = QtWidgets.QLabel(downloadUI)
        self.action_labelImg.setGeometry(QtCore.QRect(140, 130, 71, 61))
        self.action_labelImg.setText("")
        self.action_labelImg.setPixmap(QtGui.QPixmap("frontend/img/down_arrow.jpg"))
        self.action_labelImg.setScaledContents(True)
        self.action_labelImg.setObjectName("action_labelImg")

        self.cancelButton = QtWidgets.QPushButton(downloadUI)
        self.cancelButton.setGeometry(QtCore.QRect(280, 150, 75, 41))
        self.cancelButton.setObjectName("cancelButton")
        self.cancelButton.setText("Nice !")
        self.cancelButton.clicked.connect(lambda: downloadUI.close())

        # Initialize default labels if inputs are invalid
        nb_of_urls = len(urls_list)
        nb_of_destination_paths = len(destination_paths)
        if nb_of_urls == 0:
            self.state_label.setText("There are no urls to be downloaded")
            self.state_label.adjustSize()
        else:
            self.state_label.setText("There are % s urls to be downloaded" % nb_of_urls)
            self.state_label.adjustSize()

        if nb_of_destination_paths == 0:

            self.action_label.setText("There are no correct destination folder")
            self.action_label.adjustSize()
        else:
            self.action_label.setText("There are % s destination folders" % nb_of_destination_paths)
            self.action_label.adjustSize()
        self.progression_label.setText("0/" + str(nb_of_urls))
        self.progression_label.adjustSize()

        downloadUI.adjustSize()

    def download(self, urls_list, destination_folder):
        nb_of_urls = len(urls_list)
        self.state_label.setText("Currently downloading in " + destination_folder + "...")
        self.state_label.adjustSize()
        progression = 1
        for url in urls_list:
            self.action_label.setText(url)
            self.action_label.adjustSize()
            print(url)
            # dlm.dl_url_to_mp3(url, destination_paths[0])
            self.progressBar.setValue(round((progression/nb_of_urls)*100))
            self.progression_label.setText(str(progression) + "/" + str(nb_of_urls))
            self.progression_label.adjustSize()
            progression = progression + 1
            time.sleep(0.25)
            QApplication.processEvents()

    def synchronizeFiles(self, destination_paths):
        self.action_labelImg.setPixmap(QtGui.QPixmap("frontend/img/copy.png"))
        nb_of_destination_paths = len(destination_paths)
        mp3_list = os.listdir(destination_paths[0])
        nb_of_mp3 = len(mp3_list)
        if nb_of_destination_paths > 1:
            for index in range(1, (nb_of_destination_paths - 1)):
                self.state_label.setText("Currently copying from " + destination_paths[0] + " to " + destination_paths[index] + "...")
                self.state_label.adjustSize()
                progression = 1
                for mp3 in mp3_list:
                    self.action_label.setText(mp3)
                    self.action_label.adjustSize()
                    print(mp3)
                    # path_source = destination_paths[0] + "/" + filename
                    # path_destination = destination_paths[index] + "/" + filename
                    # fsm.copy(path_source, path_destination)
                    self.progressBar.setValue(round((progression/nb_of_mp3)*100))
                    self.progression_label.setText(str(progression) + "/" + str(nb_of_mp3))
                    self.progression_label.adjustSize()
                    progression = progression + 1
