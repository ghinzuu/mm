#!/usr/bin/env python

import os
from PyQt5 import QtCore, QtWidgets, QtGui
import backend.file_system_manager as fsm
import backend.cloud_manager as clm
from frontend.CloudUI import CloudUI

"""
    This manager displays all the URLS to be downloaded,
    based on the inputs provided by the user on the MusicManagerUI.

    TODO:
    - Check for browser for correct bookmarks?
    - test dl DL YT & SC
    - SoundCloud DL like page
    - Firefox favorites
    - fixed label sized
    - files remembering dl destination folders
    - test sync files
"""


class CloudManagerUI(object):
    def setupUi(self, cloudManagerUI, platform, action, fileSystemFolder):
        cloudManagerUI.setObjectName("cloudManagerUI")
        cloudManagerUI.resize(850, 950)
        cloudManagerUI.setWindowTitle("Cloud manager")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("frontend/img/mmIcon2.png"),
                       QtGui.QIcon.Normal, QtGui.QIcon.Off)
        cloudManagerUI.setWindowIcon(icon)

        self.scrollArea = QtWidgets.QScrollArea(cloudManagerUI)
        self.scrollArea.setGeometry(QtCore.QRect(10, 10, 800, 900))
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scrollArea.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOn)
        self.scrollArea.setSizeAdjustPolicy(
            QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 750, 850))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout = QtWidgets.QVBoxLayout(
            self.scrollAreaWidgetContents)
        self.verticalLayout.setObjectName("verticalLayout")

        print(platform)
        print(action)
        print(fileSystemFolder)

        self.cloudManager = None
        if platform == "Google Drive":
            self.cloudManager = clm.GoogleDriveApi()
            print("google creds")
            print(self.cloudManager.credentials)
        elif platform == "Mega":
            pass

        self.musicFolder = fileSystemFolder
        # x & y position of the differents labels on the page
        self.x_position = 30
        self.y_position = 30
        self.action = action
        self.mp3s_list = []

        title = "Download from " + platform + " to " + fileSystemFolder
        if action == "upload":
            title = "Upload from " + fileSystemFolder + " to " + platform

        syncTitle_label = self.createLabel(
            "syncTitle_label", self.x_position, self.y_position, title
        )
        font = QtGui.QFont()
        font.setPointSize(22)
        syncTitle_label.setFont(font)
        self.y_position = self.y_position + 20
        syncTitleLabelWidth = syncTitle_label.size().width()
        button_x_position = (syncTitleLabelWidth * 3)

        if fsm.isAValidPath(fileSystemFolder):

            self.nbOfFiles = 0
            if action == "download":
                self.displayMp3ListFromCloud()
            elif action == "upload":
                self.nbOfFiles = self.displayMp3ListFromFS(fileSystemFolder)

            self.actionButton = QtWidgets.QPushButton(cloudManagerUI)
            self.actionButton.setGeometry(
                QtCore.QRect(button_x_position, 70, 105, 75))
            self.actionButton.setObjectName("actionButton")
            self.actionButton.setText(action.capitalize())
            self.actionButton.clicked.connect(lambda: self.cloudUI())
        else:
            syncTitle_label.setText("Invalid path provided for file system folder : no action may performed")

        self.cancelButton = QtWidgets.QPushButton(cloudManagerUI)
        self.cancelButton.setGeometry(
            QtCore.QRect(button_x_position, 145, 105, 75))
        self.cancelButton.setObjectName("cancelButton")
        self.cancelButton.setText("Cancel")
        self.cancelButton.clicked.connect(lambda: cloudManagerUI.close())

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        # self.scrollArea.adjustSize()
        cloudManagerUI.adjustSize()

    def createLabel(self, labelVarName, x_position, y_position, labelText):
        setattr(self, labelVarName, QtWidgets.QLabel(
            self.scrollAreaWidgetContents))
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            getattr(self, labelVarName).sizePolicy().hasHeightForWidth())
        y_size = 15
        if "Title" in labelVarName:
            y_size = 30
        getattr(self, labelVarName).setSizePolicy(sizePolicy)
        getattr(self, labelVarName).setMinimumSize(QtCore.QSize(0, y_size))
        getattr(self, labelVarName).setGeometry(
            QtCore.QRect(x_position, y_position, 100, 13))
        getattr(self, labelVarName).setObjectName(labelVarName)
        getattr(self, labelVarName).setText(labelText)
        getattr(self, labelVarName).adjustSize()
        self.verticalLayout.addWidget(getattr(self, labelVarName))
        return getattr(self, labelVarName)

    def displaysItem(self, item, counter):
        labelVarName = 'item_' + str(counter) + '_label'
        self.y_position = self.y_position + 20
        self.createLabel(labelVarName, self.x_position, self.y_position, item)

    def displayMp3ListFromFS(self, musicPath):
        """
            Music folders may be messy (as any folders really), but you can
            expect it to contain artist folders that contains album folders
            that contains the song files
        """
        counter = 1
        fileCounter = 0
        for artistFolder in os.listdir(musicPath):
            self.displaysItem(artistFolder, counter)
            counter = counter + 1
            artistPath = os.path.join(musicPath, artistFolder)
            if os.path.isfile(artistPath):
                fileCounter = fileCounter + 1
            if os.path.isdir(artistPath):
                for albumFolder in os.listdir(artistPath):
                    self.displaysItem('\t' + albumFolder, counter)
                    counter = counter + 1
                    albumPath = os.path.join(artistPath, albumFolder)
                    if os.path.isfile(albumPath):
                        fileCounter = fileCounter + 1
                    if os.path.isdir(albumPath):
                        for mp3File in os.listdir(albumPath):
                            self.displaysItem('\t\t' + mp3File, counter)
                            counter = counter + 1
                            mp3Path = os.path.join(albumPath, mp3File)
                            if os.path.isfile(mp3Path):
                                fileCounter = fileCounter + 1
        return fileCounter

    def displayMp3ListFromCloud(self):
        self.mp3s_list = self.cloudManager.list_mp3s()
        counter = 1
        for mp3 in self.mp3s_list:
            self.displaysItem(mp3['name'], counter)
            counter = counter + 1

    def cloudUI(self):
        self.cloudWidget = QtWidgets.QWidget()
        cloudUI = CloudUI()

        cloudUI.setupUi(self.cloudWidget, self.cloudManager, self.action,
            self.musicFolder, self.nbOfFiles, self.mp3s_list)
        self.cloudWidget.show()

        if self.action == "download":
            cloudUI.download(self.mp3s_list, self.musicFolder)
        elif self.action == "upload":
            cloudUI.upload(self.musicFolder, self.nbOfFiles)
