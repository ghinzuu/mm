import os
import gc
import time
import random
import threading
from functools import partial

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.clock import Clock
from kivy.properties import NumericProperty, ListProperty, StringProperty, ObjectProperty
from kivy.animation import Animation

from backend.controller.file_system_manager import load_config, save_config, VALID_EXTENSIONS
from backend.controller.audio import AudioPlayer
from backend.model.Song import Song
import frontend.helper as helper


# Load KV file
kv_path = os.path.join(os.path.dirname(__file__), "kivy", "player_pc_ui.kv")
if Window.width <= helper.PHONE_WIDTH:  # phone layout
    kv_path = os.path.join(os.path.dirname(__file__), "kivy", "player_phone_ui.kv")
Builder.load_file(kv_path)


class PlayerUI(Screen):

    current_song_item = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Instantiate audio player
        self.audio_player = AudioPlayer()

        self.music_directory = load_config("music_directory") or os.getcwd()
        print(f"Selected player directory: {self.music_directory}")
        self.songs = [] # list of all readable songs
        self.number_of_songs = None
        self.music_directory_chooser_popup = None
        self.song = None # current selected song
        self.previous_song = None
        self.next_song = None
        self.edit_mode = False # for metadata
        self.extended_list_mode = False
        self.repeat_state = "repeat"
        self.playlist = None

        
    def on_kv_post(self, base_widget):
        #helper.apply_marquee(self.ids.title_status)
        # Populate the music list with the files in music_directory
        self.get_mp3s()


    def go_loaderUI(self):
        print("Switching to Loader screen...")
        helper.go_screen("loader", "left")

    @staticmethod
    def format_time(seconds):
        """Formats time in MM:SS format."""
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02}:{seconds:02}"


    def select_song(self, song, song_item=None, *args):
        """
        Handles file selection and play song immediately.
            --> animate the chosen file
            --> set metadata
            --> set previous and next song based on repeat status
            --> set next song box (desktop app)

        """

        # --- Nested helper: locate SongItem widget from filepath ---
        def find_song_item(path):
            """
            Searches visible widgets in the RecycleView for the SongItem
            whose song_path matches the given filepath.
            Returns the widget OR None if it is off-screen.
            """
            recycle_view = self.ids.music_list

            # recycle_view.children[0] = RecycleBoxLayout
            layout = recycle_view.children[0]

            for widget in layout.children:
                # Not all children necessarily have this attribute
                if hasattr(widget, "song_path") and widget.song_path == path:
                    return widget

            return None

        # If no SongItem passed (ex: next/previous), try to find it
        if song_item is None:
            song_item = find_song_item(song.filepath)

        # --- Animate underline ---
        if song_item:
            # Remove underline from previous song
            if (
                hasattr(self, "current_song_item")
                and self.current_song_item
                and self.current_song_item is not song_item
            ):
                self.current_song_item.animate_underline(False)

            # Animate underline for the new one
            song_item.animate_underline(True)
            self.current_song_item = song_item

        if self.current_song_item and self.current_song_item is not song_item:
            self.current_song_item.animate_underline(False)

        self.audio_player.load(song.filepath)
        self.song = song

        # Metadata set up
        self.ids.title_input.text = song.title
        self.ids.artist_input.text = song.artist
        self.ids.album_input.text = song.album
        self.ids.genre_input.text = song.genre
        self.ids.date_input.text = song.date
        self.ids.cover.source = song.cover
        self.ids.cover.reload()

        for field in (self.ids.title_input, self.ids.artist_input, self.ids.album_input,
              self.ids.genre_input, self.ids.date_input):
            field.cursor = (0, 0)
            field.scroll_x = 0

        # Previous and next song set up
        current_index = self.songs.index(song)
        previous_index = None
        next_index = None
        if self.repeat_state == "repeat":
            previous_index = (current_index - 1) % self.number_of_songs
            next_index = (current_index + 1) % self.number_of_songs
        elif self.repeat_state == "replay":
            previous_index = current_index
            next_index = current_index
        elif self.repeat_state == "shuffle":
            choices_previous = [i for i in range(self.number_of_songs) if i != current_index]
            previous_index = random.choice(choices_previous)
            choices_next = [i for i in range(self.number_of_songs) if i != current_index]
            next_index = random.choice(choices_next)
        self.previous_song = self.songs[previous_index]
        self.next_song = self.songs[next_index]
        
        if Window.width > helper.PHONE_WIDTH:
            # next song box only for desktop app
            self.next_song_box_setup()

        # Set total duration of the song on the slider
        total_duration = self.song.duration
        self.ids.total_time_label.text = f"{self.format_time(total_duration)}"
        self.ids.progress_slider.max = total_duration
        self.play()

    
    def next_song_box_setup(self):
        self.ids.next_song_filepath.text = os.path.basename(self.next_song.filepath)
        self.ids.next_song_title.text = self.next_song.title
        self.ids.next_song_artist.text = self.next_song.artist
        self.ids.next_song_cover.source = self.next_song.cover
        self.ids.next_song_cover.reload()


    def play(self):
        """Plays, pauses or resumes the selected song."""
        if not self.audio_player.current_song:
            print("No song selected.")
            return

        if not self.audio_player.is_playing:
            print(f"Playing: {self.audio_player.current_song}")
            self.audio_player.play()
            self.ids.play_icon.source = "frontend/img/icons/pause.png"
            self.ids.title_status.text = f"> {os.path.basename(self.audio_player.current_song)}"
            helper.apply_marquee(self.ids.title_status)
            # Move slider cursor every sec
            Clock.schedule_interval(self.update_slider, 1)

        elif self.audio_player.is_playing:
            self.audio_player.pause()
            self.ids.play_icon.source = "frontend/img/icons/play.png"
            self.ids.title_status.text = f"|| {os.path.basename(self.audio_player.current_song)}"
            helper.apply_marquee(self.ids.title_status)
    

    def previous(self):
        print("Previous song triggered")
        if self.previous_song is None or self.previous_song.filepath is None:
            self.previous_song = self.songs[-1]
        self.select_song(self.previous_song)


    def next(self):
        print("Next song triggered")
        if self.next_song is None or self.next_song.filepath is None:
            self.next_song = self.songs[0]
        self.select_song(self.next_song)


    def update_slider(self, dt=None):
        """Update the slider and time labels to reflect the current play time."""
        if self.audio_player.current_song and self.song:
            current_time = int(self.audio_player.get_current_time())
            #print(f"Get Current time is {current_time} seconds")
            formatted_current_time = self.format_time(current_time)
            self.ids.progress_slider.value = current_time
            self.ids.current_time_label.text = formatted_current_time

            # Check if song is over
            if current_time >= self.song.duration:
                print("Song ended, moving to next...")
                Clock.unschedule(self.update_slider)
                self.next()


    def seek_in_song(self, slider, touch):
        """Seeks to the chosen position in the song when the user moves the slider."""
        # Only handle touches inside the slider
        if not slider.collide_point(*touch.pos):
            return

        new_time = slider.value
        current_time = self.audio_player.get_current_time()

        # Avoid unnecessary reload if user clicked near current time
        if abs(new_time - current_time) > 0.5:  # half-second tolerance
            self.audio_player.seek(new_time)


    def edit_metadata(self):
        """Toggle metadata fields between editable and read-only mode."""
        
        print(f"self.edit_mode: {self.edit_mode}")

        # switching edit_mode
        self.edit_mode = not getattr(self, "edit_mode", False)

        for field in (self.ids.title_input, self.ids.artist_input, 
                    self.ids.album_input, self.ids.genre_input, self.ids.date_input):
            field.disabled = not self.edit_mode
            field.readonly = not self.edit_mode

        if self.edit_mode:
            self.ids.metadata_icon.source = "frontend/img/icons/save.png" 
        else: 
            self.ids.metadata_icon.source = "frontend/img/icons/edit.png"
        

        if not self.edit_mode:  # we just clicked Save
            current_time = self.audio_player.get_current_time()
            self.audio_player.unload()

            new_metadata = self.get_metadata_inputs()

            def save_and_reload():
                self.song.save_metadata(new_metadata)
                # Reload audio safely back in main thread
                from kivy.clock import mainthread
                @mainthread
                def reload_audio():
                    self.audio_player = AudioPlayer()
                    self.audio_player.load(self.song.filepath)
                    self.audio_player.seek(current_time)
                    self.audio_player.play()
                reload_audio()

            threading.Thread(target=save_and_reload, daemon=True).start()

        
    def get_metadata_inputs(self):
        """Retrieve edited metadata from text input fields."""
        return {
            "title": self.ids.title_input.text,
            "artist": self.ids.artist_input.text,
            "album": self.ids.album_input.text,
            "genre": self.ids.genre_input.text,
            "date": self.ids.date_input.text
        }
    

    def music_directory_browser(self):
        """Creates and opens the file chooser popup dynamically"""
        print("Opening file browser...")

        # Create file chooser
        filechooser = FileChooserListView(path="D:/", dirselect=True)

        # Create the "Select" button
        select_button = Button(text="Select", size_hint_y=None, height=50)
        select_button.bind(on_release=lambda instance: self.select_music_directory(filechooser))

        # Layout for the popup
        layout = BoxLayout(orientation="vertical", spacing=10)
        layout.add_widget(filechooser)
        layout.add_widget(select_button)

        # Create the popup
        self.music_directory_chooser_popup = Popup(
            title="Select Music Directory",
            content=layout,
            size_hint=(0.9, 0.9),
            auto_dismiss=False
        )
        self.music_directory_chooser_popup.open()


    def select_music_directory(self, filechooser):
        """Selects the chosen directory and saves it."""
        if filechooser.selection:
            self.music_directory = filechooser.selection[0]
            print(f"Selected directory: {self.music_directory}")
            save_config("music_directory", self.music_directory)
            self.music_directory_chooser_popup.dismiss()
            self.get_mp3s()


    def get_mp3s(self):
        """Lists all audio files and allows the user to play the selected one."""
        if not os.path.isdir(self.music_directory):
            print(f"Invalid directory: {self.music_directory}")
            return
         
        # Walk through directories and collect files
        for root, _, files in os.walk(self.music_directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in VALID_EXTENSIONS):
                    song_path = os.path.join(root, file)
                    song = Song(song_path)
                    self.songs.append(song)

        self.songs.sort(key=lambda song: song.title.lower())
        self.number_of_songs = len(self.songs)

        # Update music_list (RecycleView)
        self.ids.music_list.data = [
            {
                "text": song.title,
                "song": song
            }
            for song in self.songs
        ]

        #print(f"Found {len(songs)} songs in {self.music_directory}")
        #print(f"Updated music_list with {len(self.ids.music_list.data)} items")

 
    def toggle_repeat(self):
        #print("current state: " + self.repeat_state)
        if self.song is None or self.next_song.filepath is None:
            self.song = self.songs[0]
        current_index = self.songs.index(self.song)
        previous_index = None
        next_index = None

        if self.repeat_state == "repeat":
            self.repeat_state = "shuffle"
            self.ids.repeat_icon.source = "frontend/img/icons/shuffle.png"

            choices_previous = [i for i in range(self.number_of_songs) if i != current_index]
            previous_index = random.choice(choices_previous)
            choices_next = [i for i in range(self.number_of_songs) if i != current_index]
            next_index = random.choice(choices_next)
            
        elif self.repeat_state == "shuffle":
            self.repeat_state = "replay"
            self.ids.repeat_icon.source = "frontend/img/icons/replay.png"

            previous_index = current_index
            next_index = current_index


        elif self.repeat_state == "replay":
            self.repeat_state = "repeat"
            self.ids.repeat_icon.source = "frontend/img/icons/repeat.png"

            previous_index = (current_index - 1) % self.number_of_songs
            next_index = (current_index + 1) % self.number_of_songs

        self.previous_song = self.songs[previous_index]
        self.next_song = self.songs[next_index]

        if Window.width > helper.PHONE_WIDTH:
            # next song box only for desktop app
            self.next_song_box_setup()


    # helper to find an id string for a widget (for debugging)
    def get_widget_id(self, widget):
        for id_name, w in self.ids.items():
            if w is widget:
                return id_name
        return None


    def format_mp3_list(self):
        """Toggle between full and normal music list view with safe animations."""
        from kivy.animation import Animation

        self.extended_list_mode = not getattr(self, "extended_list_mode", False)
        list_icon = self.ids.list_icon
        player_layout = self.ids.player_layout
        music_list_container = self.ids.music_list_container

        """
        # Debug prints — remove later
        print("music_list_container ref:", music_list_container, "music_list_container id:", self.get_widget_id(music_list_container))
        print("player_layout children (top->bottom):")
        for c in player_layout.children:
            print("  child:", c, "id:", self.get_widget_id(c),
                "size_hint_y:", getattr(c, "size_hint_y", None),
                "height:", getattr(c, "height", None))
        """
                
        # safe storage of default heights/hints
        def ensure_defaults(widget):
            if not hasattr(widget, "default_height") or widget.default_height is None:
                # widget.height may be 0 at build time; try to use minimum_height if present
                widget.default_height = getattr(widget, "height", None) or getattr(widget, "minimum_height", None) or 20
            if not hasattr(widget, "default_size_hint_y"):
                widget.default_size_hint_y = widget.size_hint_y

        # collapse a widget (animate to height=0, opacity=0), disable after done
        def collapse_widget(widget):
            ensure_defaults(widget)
            # ensure numeric height to avoid None in animation
            if widget.height is None:
                widget.height = widget.default_height
            # animate collapse
            anim = Animation(opacity=0, height=0, d=0.25, t="out_quad")

            def _on_complete(anim, w):
                # set to fixed layout mode so BoxLayout doesn't try to allocate fractional hints
                w.size_hint_y = None
                w.disabled = True
                # keep height 0 after collapse
                w.height = 0

            anim.bind(on_complete=_on_complete)
            anim.start(widget)

        # expand a widget (restore height and opacity)
        def expand_widget(widget):
            ensure_defaults(widget)
            # restore size_hint_y to previous if it was stored; but we animate height first
            widget.disabled = False
            widget.size_hint_y = None  # animate via height (safer)
            # make sure start height is 0 if previously collapsed
            widget.height = getattr(widget, "height", 0) or 0
            anim = Animation(height=widget.default_height, opacity=1, d=0.25, t="out_quad")

            def _on_complete_expand(anim, w):
                # after height restored, restore the original size_hint_y so layout behaves normally
                w.size_hint_y = getattr(w, "default_size_hint_y", w.size_hint_y)
                # ensure height is the default one (cleanup)
                w.height = getattr(w, "default_height", w.height)

            anim.bind(on_complete=_on_complete_expand)
            anim.start(widget)

        # Iterate over a copy (safer if we modify layout properties)
        children_widget_copy = list(player_layout.children)

        # Whitelist by id name (extra safe) — this will catch weird identity problems
        for child_widget in children_widget_copy:
            #print("child_widget ref:", child_widget, "music_list_container id:", self.get_widget_id(child_widget))
            if child_widget == music_list_container:
                print("keeping:", child_widget)
                continue

            if self.extended_list_mode:
                print("collapsing:", child_widget)
                collapse_widget(child_widget)
            else:
                print("expanding:", child_widget)
                expand_widget(child_widget)


        # Now animate the music_list_container to take more or less space.
        # We'll animate height (safer) — set target to root_layout.height (fill) or stored default.
        ensure_defaults(music_list_container)
        if self.extended_list_mode:
            list_icon.source = "frontend/img/icons/reduce_list.png"
            target_height = player_layout.height  # fill available vertical space
        else:
            list_icon.source = "frontend/img/icons/extend_list.png"
            target_height = getattr(music_list_container, "default_height", music_list_container.height or 200)

        # ensure keep has numeric height to start
        if music_list_container.height is None or music_list_container.height == 0:
            # if currently collapsed to 0, set a sensible start
            music_list_container.height = getattr(music_list_container, "default_height", 200)
        music_list_container.disabled = False
        # animate fill/restore
        Animation(height=target_height, d=0.28, t="out_quad").start(music_list_container)

        # final debug
        print("toggled extended_list_mode ->", self.extended_list_mode)


    def sampler(self):
        print("TODO: sampler")


    def search(self, *args):
        """Filters the songs list according to the search input."""
        query = self.ids.search_input.text.strip().lower()

        # If query is empty → show everything
        if not query:
            self.filtered_songs = self.songs[:]
        else:
            self.filtered_songs = []

            for song in self.songs:
                fields = [
                    song.filename.lower(),
                    song.title.lower() if song.title else "",
                    song.artist.lower() if song.artist else "",
                    song.album.lower() if song.album else "",
                    song.genre.lower() if song.genre else "",
                    song.date.lower() if isinstance(song.date, str) else str(song.date)
                ]

                # Match if ANY field contains the query
                if any(query in field for field in fields):
                    self.filtered_songs.append(song)

        # Update music_list RecycleView
        self.ids.music_list.data = [
            {
                "text": song.title,
                "song": song
            }
            for song in self.filtered_songs
        ]


    def list_playlists(self):
        popup = self.factory.PlaylistPopup()
        self.playlist_popup = popup

        playlists = self.playlist_db.list_playlists()

        popup.ids.playlist_rv.data = [
            {"playlist_name": name} for name in playlists
        ]

        popup.open()


    def select_playlist(self, playlist_name):
        self.playlist = playlist_name
        print(f"Selected playlist: {playlist_name}")


    def delete_playlist(self, name):
        self.playlist_db.delete_playlist(name)
        self.list_playlist_function()  # refresh popup


    def create_playlist(self):
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        input_name = TextInput(hint_text="Playlist name", multiline=False)

        def confirm(instance):
            name = input_name.text.strip()
            if not name:
                return
            try:
                self.playlist_db.add_playlist(name)
                popup.dismiss()
                self.list_playlist_function()
            except Exception:
                print("Playlist already exists")

        content.add_widget(input_name)
        content.add_widget(Button(text="Create", on_release=confirm))

        popup = Popup(
            title="New playlist",
            content=content,
            size_hint=(0.6, 0.4),
        )
        popup.open()


class SongItem(helper.LightButton):
    underline_width = NumericProperty(0)
    underline_color = ListProperty([0.35, 0.70, 0.64, 1])
    song_path = StringProperty("") 

    def animate_underline(self, focused):
        if focused:
            Animation(underline_width=self.width, d=0.2, t="out_quad").start(self)
        else:
            Animation(underline_width=0, d=0.2, t="out_quad").start(self)

    def on_release(self):
        # find the PlayerUI parent
        player_ui = self.get_player_ui()
        if player_ui:
            player_ui.select_song(self.song, self)

    def get_player_ui(self):
        # climb up until we find PlayerUI
        parent = self.parent
        while parent and not isinstance(parent, PlayerUI):
            parent = parent.parent
        return parent


class PlaylistItem(BoxLayout):
    playlist_name = StringProperty("")
    #selected = BooleanProperty(False)

    def on_select(self):
        player_ui = self.get_player_ui()
        if player_ui:
            player_ui.select_playlist(self.playlist_name)

    def on_delete(self):
        player_ui = self.get_player_ui()
        if player_ui:
            player_ui.delete_playlist(self.playlist_name)

    def get_player_ui(self):
        # climb up until we find PlayerUI
        parent = self.parent
        while parent and not isinstance(parent, PlayerUI):
            parent = parent.parent
        return parent


class PlayerApp(App):
    def build(self):
        return PlayerUI()

