#!/usr/bin/env python

from PyQt5 import QtCore, QtWidgets, QtGui
import backend.file_system_manager as fsm


class PathsTestingUI(object):
    def setupUi(self, pathsTestingUI, paths):
        pathsTestingUI.setObjectName("PathsTestingUI")
        pathsTestingUI.resize(390, 219)
        pathsTestingUI.setWindowTitle("Path testing")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("frontend/img/mmIcon2.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        pathsTestingUI.setWindowIcon(icon)

        print(paths)

        index = 1
        y_position = 10
        for path in paths.split('?'):
            print(path)
            pathVarName = 'path' + str(index) + '_label'
            y_position = y_position + 20
            setattr(self, pathVarName, QtWidgets.QLabel(pathsTestingUI))
            getattr(self, pathVarName).setGeometry(QtCore.QRect(30, y_position, 47, 13))
            getattr(self, pathVarName).setObjectName(pathVarName)
            getattr(self, pathVarName).setText(path)
            getattr(self, pathVarName).adjustSize()

            result = 'Path is not valid'
            background_color = "background-color: red"
            if fsm.isAValidPath(path):
                result = 'Path is valid'
                background_color = "background-color: lightgreen"

            resultVarName = 'result' + str(index) + '_label'
            y_position = y_position + 20
            setattr(self, resultVarName, QtWidgets.QLabel(pathsTestingUI))
            getattr(self, resultVarName).setGeometry(QtCore.QRect(30, y_position, 47, 13))
            getattr(self, resultVarName).setObjectName(resultVarName)
            getattr(self, resultVarName).setText(result)
            getattr(self, resultVarName).setStyleSheet(background_color)
            getattr(self, resultVarName).adjustSize()

            index = index + 1

        self.alrightButton = QtWidgets.QPushButton(pathsTestingUI)
        self.alrightButton.setGeometry(QtCore.QRect(280, 180, 75, 23))
        self.alrightButton.setObjectName("alrightButton")
        self.alrightButton.setText("Alright")
        self.alrightButton.clicked.connect(lambda: pathsTestingUI.close())

        pathsTestingUI.adjustSize()
