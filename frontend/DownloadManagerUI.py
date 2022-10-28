#!/usr/bin/env python

from PyQt5 import QtCore, QtWidgets, QtGui
import backend.file_system_manager as fsm
from frontend.DownloadUI import DownloadUI

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


class DownloadManagerUI(object):
    def setupUi(self, downloadManagerUI, downloadData):
        downloadManagerUI.setObjectName("downloadManagerUI")
        downloadManagerUI.resize(850, 950)
        downloadManagerUI.setWindowTitle("Download manager")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("frontend/img/mmIcon2.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        downloadManagerUI.setWindowIcon(icon)

        print("downloadData : ")
        print("soloUrl : " + str(downloadData.isSoloUrlChecked) + " " + downloadData.soloUrl)
        print("Are Chrome/Firefox/Brave Checked : "
            + str(downloadData.isChromeFavoriteChecked) + " "
            + str(downloadData.isFirefoxFavoriteChecked) + " "
            + str(downloadData.isBraveFavoriteChecked))
        print("favFolderName : " + downloadData.favFolderName)
        print("scPageUrl : " + str(downloadData.isScPageChecked) + " " + downloadData.scPageUrl)
        print("destinationPaths : " + downloadData.destinationPaths)

        self.scrollArea = QtWidgets.QScrollArea(downloadManagerUI)
        self.scrollArea.setGeometry(QtCore.QRect(10, 10, 800, 900))
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scrollArea.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 750, 850))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setObjectName("verticalLayout")

        self.urls_list = []
        self.urls_names = {}
        default_paths = fsm.get_default_urls_paths()

        if downloadData.isChromeFavoriteChecked:
            self.urls_list, self.urls_names = fsm.get_urls(
                    default_paths["chrome_bookmarks_path"],
                    downloadData.favFolderName
                )

        # TODO
        if downloadData.isFirefoxFavoriteChecked:
            pass

        if downloadData.isBraveFavoriteChecked:
            temp_list, temp_dict = fsm.get_urls(
                    default_paths["brave_bookmarks_path"],
                    downloadData.favFolderName
                )
            self.urls_list = self.urls_list + temp_list
            self.urls_names = self.urls_names | temp_dict

        if downloadData.isSoloUrlChecked:
            self.urls_list.append(downloadData.soloUrl)

        # TODO
        if downloadData.isScPageChecked:
            pass

        # print(self.urls_list)

        # x & y position of the differents labels on the page
        x_position = 30
        y_position = 30

        urlTitle_label = self.createLabel(
            "urlTitle_label", x_position, y_position,
            "The followings URLs will be downloaded:")
        font = QtGui.QFont()
        font.setPointSize(22)
        urlTitle_label.setFont(font)
        # this y_position increment is to handle the fact that the title is big,
        # so +40 is needed between title and 1st label
        y_position = y_position + 20

        index = 1
        for url in self.urls_list:
            # print("url:")
            # print(url)
            urlVarName = 'url' + str(index) + '_label'
            y_position = y_position + 20
            urlName = ""
            if url in self.urls_names:
                urlName = self.urls_names[url] + " - "
            urlLabelText = str(index) + " - " + urlName + url
            self.createLabel(urlVarName, x_position, y_position, urlLabelText)
            index = index + 1

        destPathsTitle_label = self.createLabel(
            "destPathsTitle_label", x_position, y_position,
            "Files will be downloaded in the following(s) repository(ies)")
        font = QtGui.QFont()
        font.setPointSize(22)
        destPathsTitle_label.setFont(font)
        y_position = y_position + 20

        index = 1
        self.valid_paths = []
        for path in downloadData.destinationPaths.split('?'):
            # print(path)
            pathVarName = 'path' + str(index) + '_label'
            y_position = y_position + 20
            result = ' : Invalid path'
            background_color = "background-color: red"
            if fsm.isAValidPath(path):
                self.valid_paths.append(path)
                result = ' : Valid path'
                background_color = "background-color: lightgreen"
            pathLabel = self.createLabel(pathVarName, x_position, y_position, path + result)
            pathLabel.setStyleSheet(background_color)
            index = index + 1

        urlTitleLabelWidth = urlTitle_label.size().width()
        button_x_position = (urlTitleLabelWidth * 3)

        self.dlButton = QtWidgets.QPushButton(downloadManagerUI)
        self.dlButton.setGeometry(QtCore.QRect(button_x_position, 70, 105, 75))
        self.dlButton.setObjectName("dlButton")
        self.dlButton.setText("Download !")
        self.dlButton.clicked.connect(lambda: self.downloadUI())

        self.cancelButton = QtWidgets.QPushButton(downloadManagerUI)
        self.cancelButton.setGeometry(QtCore.QRect(button_x_position, 145, 105, 75))
        self.cancelButton.setObjectName("cancelButton")
        self.cancelButton.setText("Cancel")
        self.cancelButton.clicked.connect(lambda: downloadManagerUI.close())

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        # self.scrollArea.adjustSize()
        downloadManagerUI.adjustSize()

    def createLabel(self, labelVarName, x_position, y_position, labelText):
        setattr(self, labelVarName, QtWidgets.QLabel(self.scrollAreaWidgetContents))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(getattr(self, labelVarName).sizePolicy().hasHeightForWidth())
        y_size = 15
        if "Title" in labelVarName:
            y_size = 30
        getattr(self, labelVarName).setSizePolicy(sizePolicy)
        getattr(self, labelVarName).setMinimumSize(QtCore.QSize(0, y_size))
        getattr(self, labelVarName).setGeometry(QtCore.QRect(x_position, y_position, 100, 13))
        getattr(self, labelVarName).setObjectName(labelVarName)
        getattr(self, labelVarName).setText(labelText)
        getattr(self, labelVarName).adjustSize()
        self.verticalLayout.addWidget(getattr(self, labelVarName))
        return getattr(self, labelVarName)

    def downloadUI(self):
        self.downloadWidget = QtWidgets.QWidget()
        downloadUI = DownloadUI()
        nb_of_urls = len(self.urls_list)
        nb_of_destination_paths = len(self.valid_paths)
        downloadUI.setupUi(self.downloadWidget, self.urls_list, self.valid_paths)
        self.downloadWidget.show()

        if nb_of_urls != 0 and nb_of_destination_paths != 0:
            downloadUI.download(self.urls_list, self.valid_paths[0])
            if nb_of_destination_paths > 1:
                downloadUI.synchronizeFiles(self.valid_paths)
