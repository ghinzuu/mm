#!/usr/bin/env python

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QApplication
import os

"""
    This manager displays all the URLS to be downloaded,
    based on the inputs provided by the user on the MusicManagerUI.
"""


# need picture for upload/download
class CloudUI(object):
    def setupUi(self, cloudUI, cloudManager, action, musicFolder, counter, mp3s_list):
        cloudUI.setObjectName("cloudUI")
        cloudUI.resize(393, 235)
        # if action == "download"
        title = "Download from cloud"
        actionImage = "frontend/img/down_arrow.jpg"
        if action == "upload":
            title = "Upload to cloud"
            actionImage = "frontend/img/up_arrow.jpg"
        cloudUI.setWindowTitle(title)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("frontend/img/mmIcon2.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        cloudUI.setWindowIcon(icon)

        self.state_label = QtWidgets.QLabel(cloudUI)
        self.state_label.setGeometry(QtCore.QRect(30, 20, 321, 16))
        self.state_label.setObjectName("state_label")

        self.action_label = QtWidgets.QLabel(cloudUI)
        self.action_label.setGeometry(QtCore.QRect(30, 50, 321, 16))
        self.action_label.setObjectName("action_label")

        self.progression_label = QtWidgets.QLabel(cloudUI)
        self.progression_label.setGeometry(QtCore.QRect(310, 90, 41, 16))
        self.progression_label.setObjectName("progression_label")

        self.progressBar = QtWidgets.QProgressBar(cloudUI)
        self.progressBar.setGeometry(QtCore.QRect(30, 90, 261, 23))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")

        self.action_labelImg = QtWidgets.QLabel(cloudUI)
        self.action_labelImg.setGeometry(QtCore.QRect(140, 130, 71, 61))
        self.action_labelImg.setText("")
        self.action_labelImg.setPixmap(QtGui.QPixmap(actionImage))
        self.action_labelImg.setScaledContents(True)
        self.action_labelImg.setObjectName("action_labelImg")

        self.cancelButton = QtWidgets.QPushButton(cloudUI)
        self.cancelButton.setGeometry(QtCore.QRect(280, 150, 75, 41))
        self.cancelButton.setObjectName("cancelButton")
        self.cancelButton.setText("Let's go !")
        self.cancelButton.clicked.connect(lambda: cloudUI.close())

        # Initialize default labels if inputs are invalid
        nb_of_urls = len(mp3s_list)
        if nb_of_urls == 0 and action == "download":
            self.state_label.setText("There are no urls to be downloaded")
            self.state_label.adjustSize()
        else:
            self.state_label.setText("There are % s urls to be downloaded" % nb_of_urls)
            self.state_label.adjustSize()

        if not musicFolder:
            self.action_label.setText("There are no correct music folder")
            self.action_label.adjustSize()
        else:
            self.action_label.setText("The file system folder is " + musicFolder)
            self.action_label.adjustSize()
        self.progression_label.setText("0/" + str(nb_of_urls))
        self.progression_label.adjustSize()

        self.cloudManager = cloudManager

        cloudUI.adjustSize()

    def updateStatus(self, text, progression, nbOfFiles):
        self.action_label.setText(text)
        self.action_label.adjustSize()
        print("updateStatus")
        self.progressBar.setValue(round((progression/nbOfFiles)*100))
        self.progression_label.setText(str(progression) + "/" + str(nbOfFiles))
        self.progression_label.adjustSize()
        progression = progression + 1
        QApplication.processEvents()
        return progression

    # /!\ Needs to be tested
    def download(self, mp3sList, musicFolder):
        self.state_label.setText("Currently downloading from your cloud to " + musicFolder + " ...")
        self.state_label.adjustSize()
        QApplication.processEvents()
        progression = 1
        nbOfMp3 = len(mp3sList)
        for mp3 in mp3sList:
            self.cloudManager.download_mp3(mp3, musicFolder)
            progression = self.updateStatus(mp3['name'], progression, nbOfMp3)

    # /!\ Needs to be tested
    def upload(self, musicPath, nbOfFiles):
        self.state_label.setText("Currently uploading from " + musicPath + " to your cloud...")
        self.state_label.adjustSize()
        QApplication.processEvents()
        progression = 1
        print(musicPath + ' ' + str(nbOfFiles))
        # musicPath/artistFolder/albumFolder/mp3File
        for artistFolder in os.listdir(musicPath):
            artistPath = os.path.join(musicPath, artistFolder)
            if os.path.isfile(artistPath):
                progression = self.updateStatus(artistFolder, progression, nbOfFiles)
                self.cloudManager.upload_mp3(artistPath)
            elif os.path.isdir(artistPath):
                for albumFolder in os.listdir(artistPath):
                    albumPath = os.path.join(artistPath, albumFolder)
                    if os.path.isfile(albumPath):
                        progression = self.updateStatus(albumFolder, progression, nbOfFiles)
                        self.cloudManager.upload_mp3(albumPath)
                    if os.path.isdir(albumPath):
                        for mp3File in os.listdir(albumPath):
                            mp3Path = os.path.join(albumPath, mp3File)
                            progression = self.updateStatus(mp3File, progression, nbOfFiles)
                            self.cloudManager.upload_mp3(mp3Path)
        # for artistFolder in os.listdir(musicPath):
        #     artistPath = os.path.join(musicPath, artistFolder)
        #     progression = self.updateStatus(artistFolder, progression, nbOfFiles)
        #     print(artistFolder + " is a file1")
        #     self.cloudManager.upload_mp3(artistPath)
        #     QApplication.processEvents()
