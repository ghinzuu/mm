#!/usr/bin/env python

"""
    The purposes of this manager are :
        - Update metadata of the music files:
            * Current downloaded files
            * Already owned files
        - Generate music stats:
            * number of times a music is listened to
            * dates listening
            * number of times gender is listen to
        - Generate playlists:
            * based on gender
            * based on popularity
            * isolate music sets (30 min+ songs)
        - Set editor :
            * cuts parts of songs
            * assemble parts of songs
        - App users :
            * private messages
            * common forum
    This will most likely need a DB to be functionnal.
"""
