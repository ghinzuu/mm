#!/usr/bin/env python

from PyQt5 import QtCore, QtWidgets  # QtGui
import backend.file_system_manager as fsm
import backend.cloud_manager as clm


class CloudConnectUI(object):
    def setupUi(self, cloudConnectUI, platform):
        cloudConnectUI.setObjectName("cloudConnectUI")
        cloudConnectUI.resize(390, 219)
        print(platform)
        cloudConnectUI.setWindowTitle(platform + " connection")
        # clm.google_drive_connection()
        clm.google_cloud()
        connectionResult = "Connection successful! You can download from/upload to your Google drive"
        self.connectionResult = QtWidgets.QLabel(cloudConnectUI)
        self.connectionResult.setGeometry(QtCore.QRect(30, 30, 47, 13))
        self.connectionResult.setObjectName("connection")
        self.connectionResult.setText(connectionResult)
        self.connectionResult.adjustSize()

        self.alrightButton = QtWidgets.QPushButton(cloudConnectUI)
        self.alrightButton.setGeometry(QtCore.QRect(280, 180, 75, 23))
        self.alrightButton.setObjectName("alrightButton")
        self.alrightButton.setText("Alright")
        self.alrightButton.clicked.connect(lambda: cloudConnectUI.close())

        cloudConnectUI.adjustSize()
