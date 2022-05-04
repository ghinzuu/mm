#!/usr/bin/env python


"""
    The purpose of this class is to send a set of parameters from the
    MusicManagerUI to the DownloadManagerUI.
"""


class DownloadManagerData():
    def __init__(
        self, isSoloUrlChecked, soloUrl,
        isChromeFavoriteChecked, isFirefoxFavoriteChecked,
        isBraveFavoriteChecked, favFolderName,
        isScPageChecked, scPageUrl,
        destinationPaths
    ):
        self.isSoloUrlChecked = isSoloUrlChecked
        self.soloUrl = soloUrl
        self.isChromeFavoriteChecked = isChromeFavoriteChecked
        self.isFirefoxFavoriteChecked = isFirefoxFavoriteChecked
        self.isBraveFavoriteChecked = isBraveFavoriteChecked
        self.favFolderName = favFolderName
        self.isScPageChecked = isScPageChecked
        self.scPageUrl = scPageUrl
        self.destinationPaths = destinationPaths
