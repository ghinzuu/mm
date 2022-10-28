#!/usr/bin/env python

# import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from functools import partial

import backend.file_system_manager as fsm

from frontend.PathsTestingUI import PathsTestingUI
from frontend.CloudConnectUI import CloudConnectUI
from frontend.DownloadManagerData import DownloadManagerData
from frontend.DownloadManagerUI import DownloadManagerUI
from frontend.CloudManagerUI import CloudManagerUI


"""
    This UI is the general UI of the application.
    It is kind of a mess, I formally apologize for that.
    I have not figured out yet how to make this clearer, hopefully this comment will.

    I have tried to order every elements of the UI from top to bottom
    in the code like it is in the UI, for each UI in the app.

    Several buttons triggers new screens that can also trigger new screens.
    Basically the MusicManager manages all the different managers the app features,
    like an orchestra maestro. All these specific managers will provide a recap
    of the action to be performed. If confirmed the underlying manager will display
    a screen that shows the action being performed.
    I.E. :
    --> On the MusicManagerUI, users clicks the 'Download Manager' button.
    --> DownloadManagerUI pops, displaying all urls to be downloaded, and destination folders.
    --> Once confirmed, DownloadManagerUI pops the DownloadUI displaying each link being currently downloaded.

    TODO:
        - youtube playlist downloader --yes-playlist
        - enable video downloads
        - remove the 'testPaths & testCloud buttons'
        - DLM almost done
        - Cloud :
            - Google Drive
            - Mega
        - Check UI resize & and mobile format
"""


class MusicManagerUI(object):

    def setupUi(self, MusicManagerUI):
        MusicManagerUI.setObjectName("MusicManagerUI")
        MusicManagerUI.setEnabled(True)
        MusicManagerUI.resize(516, 563)
        MusicManagerUI.setMouseTracking(True)
        MusicManagerUI.setAutoFillBackground(False)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("frontend/img/mmIcon2.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MusicManagerUI.setWindowIcon(icon)
        self.centralwidget = QtWidgets.QWidget(MusicManagerUI)
        self.centralwidget.setObjectName("centralwidget")
        MusicManagerUI.setCentralWidget(self.centralwidget)

        self.menubar = QtWidgets.QMenuBar(MusicManagerUI)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 781, 21))
        self.menubar.setObjectName("menubar")
        MusicManagerUI.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MusicManagerUI)
        self.statusbar.setObjectName("statusbar")
        MusicManagerUI.setStatusBar(self.statusbar)

        # Dowload Manager button
        self.dlButton = QtWidgets.QPushButton(self.centralwidget)
        self.dlButton.setGeometry(QtCore.QRect(350, 10, 121, 151))
        self.dlButton.setAutoFillBackground(False)
        self.dlButton.setObjectName("dlButton")
        self.dlButton.clicked.connect(self.downloadManagerUI)

        # Downloads checkboxes
        self.dlUrl_cb = QtWidgets.QCheckBox(self.centralwidget)
        self.dlUrl_cb.setGeometry(QtCore.QRect(30, 10, 261, 17))
        self.dlUrl_cb.setObjectName("dlUrl_cb")

        self.chromeFav_cb = QtWidgets.QCheckBox(self.centralwidget)
        self.chromeFav_cb.setGeometry(QtCore.QRect(30, 60, 61, 17))
        self.chromeFav_cb.setObjectName("chromeFav_cb")

        self.braveFav_cb = QtWidgets.QCheckBox(self.centralwidget)
        self.braveFav_cb.setGeometry(QtCore.QRect(90, 60, 51, 17))
        self.braveFav_cb.setObjectName("braveFav_cb")

        self.firefoxFav_cb = QtWidgets.QCheckBox(self.centralwidget)
        self.firefoxFav_cb.setGeometry(QtCore.QRect(140, 60, 61, 17))
        self.firefoxFav_cb.setObjectName("firefoxFav_cb")

        self.favFolder_label = QtWidgets.QLabel(self.centralwidget)
        self.favFolder_label.setGeometry(QtCore.QRect(200, 60, 111, 16))
        self.favFolder_label.setObjectName("favFolder_label")

        self.dlScList_cb = QtWidgets.QCheckBox(self.centralwidget)
        self.dlScList_cb.setGeometry(QtCore.QRect(30, 110, 171, 17))
        self.dlScList_cb.setObjectName("dlScList_cb")

        # Downloads lines
        self.dlUrl_line = QtWidgets.QLineEdit(self.centralwidget)
        self.dlUrl_line.setGeometry(QtCore.QRect(20, 30, 311, 21))
        self.dlUrl_line.setObjectName("dlUrl_line")

        self.favFolder_line = QtWidgets.QLineEdit(self.centralwidget)
        self.favFolder_line.setGeometry(QtCore.QRect(20, 80, 311, 21))
        self.favFolder_line.setObjectName("favFolder_line")

        self.dlScList_line = QtWidgets.QLineEdit(self.centralwidget)
        self.dlScList_line.setGeometry(QtCore.QRect(20, 130, 311, 21))
        self.dlScList_line.setObjectName("dlScList_line")

        # File system
        self.destinationPaths_label = QtWidgets.QLabel(self.centralwidget)
        self.destinationPaths_label.setGeometry(QtCore.QRect(30, 170, 291, 20))
        self.destinationPaths_label.setObjectName("destinationPaths_label")

        self.destinationPaths_line = QtWidgets.QLineEdit(self.centralwidget)
        self.destinationPaths_line.setGeometry(QtCore.QRect(20, 190, 451, 21))
        self.destinationPaths_line.setObjectName("destinationPaths_line")

        self.testPathsButton = QtWidgets.QPushButton(self.centralwidget)
        self.testPathsButton.setGeometry(QtCore.QRect(340, 220, 121, 23))
        self.testPathsButton.setObjectName("testPathsButton")
        self.testPathsButton.clicked.connect(self.testPathsUI)

        # Cloud
        self.cloud_label = QtWidgets.QLabel(self.centralwidget)
        self.cloud_label.setGeometry(QtCore.QRect(30, 220, 41, 16))
        self.cloud_label.setObjectName("cloud_label")

        self.gDrive_radioB = QtWidgets.QRadioButton(self.centralwidget)
        self.gDrive_radioB.setGeometry(QtCore.QRect(70, 220, 82, 17))
        self.gDrive_radioB.setAutoFillBackground(True)
        self.gDrive_radioB.setChecked(True)
        self.gDrive_radioB.setObjectName("gDrive_radioB")

        self.mega_radioB = QtWidgets.QRadioButton(self.centralwidget)
        self.mega_radioB.setGeometry(QtCore.QRect(160, 220, 82, 17))
        self.mega_radioB.setObjectName("mega_radioB")

        self.cloudConnectButton = QtWidgets.QPushButton(self.centralwidget)
        self.cloudConnectButton.setGeometry(QtCore.QRect(210, 220, 121, 23))
        self.cloudConnectButton.setObjectName("cloudConnectButton")
        self.cloudConnectButton.clicked.connect(self.cloudConnectUI)

        self.syncFsToCloudButton = QtWidgets.QPushButton(self.centralwidget)
        self.syncFsToCloudButton.setGeometry(QtCore.QRect(20, 250, 451, 61))
        self.syncFsToCloudButton.setObjectName("syncFsToCloudButton")
        self.syncFsToCloudButton.clicked.connect(partial(self.cloudManagerUI, "syncFsToCloudButton"))

        self.syncCloudToFsButton = QtWidgets.QPushButton(self.centralwidget)
        self.syncCloudToFsButton.setGeometry(QtCore.QRect(20, 390, 461, 61))
        self.syncCloudToFsButton.setObjectName("syncCloudToFsButton")
        self.syncCloudToFsButton.clicked.connect(partial(self.cloudManagerUI, "syncCloudToFsButton"))

        # Images
        self.comp1_labelImg = QtWidgets.QLabel(self.centralwidget)
        self.comp1_labelImg.setGeometry(QtCore.QRect(100, 310, 81, 81))
        self.comp1_labelImg.setText("")
        self.comp1_labelImg.setPixmap(QtGui.QPixmap("frontend/img/computer.png"))
        self.comp1_labelImg.setScaledContents(True)
        self.comp1_labelImg.setObjectName("comp1_labelImg")

        self.right1_labelImg = QtWidgets.QLabel(self.centralwidget)
        self.right1_labelImg.setGeometry(QtCore.QRect(200, 320, 71, 61))
        self.right1_labelImg.setText("")
        self.right1_labelImg.setPixmap(QtGui.QPixmap("frontend/img/right-arrow.jpg"))
        self.right1_labelImg.setScaledContents(True)
        self.right1_labelImg.setObjectName("right1_labelImg")

        self.cloud1_labelImg = QtWidgets.QLabel(self.centralwidget)
        self.cloud1_labelImg.setGeometry(QtCore.QRect(290, 320, 81, 61))
        self.cloud1_labelImg.setText("")
        self.cloud1_labelImg.setPixmap(QtGui.QPixmap("frontend/img/cloud.png"))
        self.cloud1_labelImg.setScaledContents(True)
        self.cloud1_labelImg.setObjectName("cloud1_labelImg")

        self.cloud2_labelImg = QtWidgets.QLabel(self.centralwidget)
        self.cloud2_labelImg.setGeometry(QtCore.QRect(100, 460, 81, 61))
        self.cloud2_labelImg.setText("")
        self.cloud2_labelImg.setPixmap(QtGui.QPixmap("frontend/img/cloud.png"))
        self.cloud2_labelImg.setScaledContents(True)
        self.cloud2_labelImg.setObjectName("cloud2_labelImg")

        self.right2_labelImg = QtWidgets.QLabel(self.centralwidget)
        self.right2_labelImg.setGeometry(QtCore.QRect(200, 460, 71, 61))
        self.right2_labelImg.setText("")
        self.right2_labelImg.setPixmap(QtGui.QPixmap("frontend/img/right-arrow.jpg"))
        self.right2_labelImg.setScaledContents(True)
        self.right2_labelImg.setObjectName("right2_labelImg")

        self.comp2_labelImg = QtWidgets.QLabel(self.centralwidget)
        self.comp2_labelImg.setGeometry(QtCore.QRect(290, 450, 81, 81))
        self.comp2_labelImg.setText("")
        self.comp2_labelImg.setPixmap(QtGui.QPixmap("frontend/img/computer.png"))
        self.comp2_labelImg.setScaledContents(True)
        self.comp2_labelImg.setObjectName("comp2_labelImg")

        self.retranslateUi(MusicManagerUI)
        QtCore.QMetaObject.connectSlotsByName(MusicManagerUI)

    def retranslateUi(self, MusicManagerUI):
        _translate = QtCore.QCoreApplication.translate
        MusicManagerUI.setWindowTitle(_translate("MusicManagerUI", "Music Manager"))

        self.dlButton.setText(_translate("MusicManagerUI", "Download Manager"))

        self.dlUrl_cb.setText(_translate("MusicManagerUI", "Single Link to download (Youtube or SoundCloud)"))
        self.chromeFav_cb.setText(_translate("MusicManagerUI", "Chrome"))
        self.braveFav_cb.setText(_translate("MusicManagerUI", "Brave"))
        self.firefoxFav_cb.setText(_translate("MusicManagerUI", "Firefox"))
        self.favFolder_label.setText(_translate("MusicManagerUI", "(Browser folder name)"))
        self.dlScList_cb.setText(_translate("MusicManagerUI", "SoundCloud likes/playlist page"))

        self.dlUrl_line.setText(_translate("MusicManagerUI", "https://www.youtube.com/watch?v=zU97FbKVH_c"))
        self.favFolder_line.setText(_translate("MusicManagerUI", "music"))
        self.dlScList_line.setText(_translate("MusicManagerUI", "https://soundcloud.com/you/likes"))

        self.destinationPaths_label.setText(_translate("MusicManagerUI", "File system folders (separated with \'?\')"))
        self.destinationPaths_line.setText(_translate("MusicManagerUI", fsm.get_saved_destination_folders()))
        self.testPathsButton.setText(_translate("MusicManagerUI", "Test path(s)"))

        self.cloud_label.setText(_translate("MusicManagerUI", "Cloud"))
        self.gDrive_radioB.setText(_translate("MusicManagerUI", "Google Drive"))
        self.mega_radioB.setText(_translate("MusicManagerUI", "Mega"))
        self.cloudConnectButton.setText(_translate("MusicManagerUI", "Test cloud connection"))
        self.syncFsToCloudButton.setText(_translate("MusicManagerUI", "Synchronize from file system to cloud"))
        self.syncCloudToFsButton.setText(_translate("MusicManagerUI", "Synchronize from cloud to file system"))

    def downloadManagerUI(self):
        fsm.save_destination_folders(self.destinationPaths_line.text())

        self.downloadData = DownloadManagerData(
            self.dlUrl_cb.isChecked(), self.dlUrl_line.text(),
            self.chromeFav_cb.isChecked(), self.firefoxFav_cb.isChecked(),
            self.braveFav_cb.isChecked(), self.favFolder_line.text(),
            self.dlScList_cb.isChecked(), self.dlScList_line.text(),
            self.destinationPaths_line.text()
        )

        self.downloadManagerWidget = QtWidgets.QWidget()
        downloadManagerUI = DownloadManagerUI()
        downloadManagerUI.setupUi(self.downloadManagerWidget, self.downloadData)
        self.downloadManagerWidget.show()

    def cloudManagerUI(self, button_name):
        fsm.save_destination_folders(self.destinationPaths_line.text())

        self.cloudManagerWidget = QtWidgets.QWidget()
        platform = "Google Drive"
        if self.mega_radioB.isChecked():
            platform = "Mega"
        action = "download"
        if button_name == "syncFsToCloudButton":
            action = "upload"
        fileSystemFolder = self.destinationPaths_line.text().split('?')[0]
        cloudManagerUI = CloudManagerUI()
        cloudManagerUI.setupUi(
            self.cloudManagerWidget,
            platform,
            action,
            fileSystemFolder
        )
        self.cloudManagerWidget.show()

    def testPathsUI(self):
        self.pathsTestingWidget = QtWidgets.QWidget()
        pathsTestingUI = PathsTestingUI()
        pathsTestingUI.setupUi(self.pathsTestingWidget, self.destinationPaths_line.text())
        self.pathsTestingWidget.show()

    def cloudConnectUI(self):
        self.cloudConnectWidget = QtWidgets.QWidget()
        cloudConnectUI = CloudConnectUI()
        platform = "Google Drive"
        cloudConnectUI.setupUi(self.cloudConnectWidget, platform)
        self.cloudConnectWidget.show()


"""
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
"""
