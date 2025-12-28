import os

"""
@author : Ghinzu

Own your music.

"""

# The followings are for development purposes

# Must come before importing anything from kivy
# Test for phone screen size
from kivy.config import Config
from screeninfo import get_monitors

# pick the right monitor 
right_monitor = get_monitors()[0]

# app width and height (phone like): 
APP_W, APP_H = 250, 540
#APP_W, APP_H = 1000, 1000

# compute centered position
pos_x = right_monitor.x + (right_monitor.width  - APP_W) // 2
pos_y = right_monitor.y + (right_monitor.height - APP_H) // 2

Config.set('graphics', 'width',  str(APP_W))
Config.set('graphics', 'height', str(APP_H))
Config.set('graphics', 'position', 'custom')
Config.set('graphics', 'left', str(pos_x))
Config.set('graphics', 'top',  str(pos_y))

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout

from frontend.player import PlayerUI
from frontend.loader import LoaderUI


kv_path = os.path.join(os.path.dirname(__file__), "frontend", "kivy", "music_manager.kv")
Builder.load_file(kv_path)

class MusicManagerAppLayout(BoxLayout):
    pass

class MusicManagerApp(App):

    icon = "frontend/img/mmIcon.png"  

    def build(self):
        return MusicManagerAppLayout()

if __name__ == "__main__":
    MusicManagerApp().run()
