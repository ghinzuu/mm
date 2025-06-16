import os
import gc
import time
from functools import partial
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.clock import Clock
from backend.file_system_manager import load_config, save_config
from backend.audio import AudioPlayer
from backend.model.Song import Song

# Load KV file
kv_path = os.path.join(os.path.dirname(__file__), "kv", "playerUI.kv")
Builder.load_file(kv_path)


class PlayerUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Instantiate audio player
        self.audio_player = AudioPlayer()

        # Hides dropdown_settings on start
        self.dropdown_settings = self.ids.dropdown_settings.__self__
        self.dropdown_settings.dismiss()

        # Populate the music list with the files in music_directory
        self.music_directory = load_config("music_directory") or os.getcwd()
        print(f"Selected directory: {self.music_directory}")
        self.songs_list = []
        self.number_of_songs = None
        self.list_files()
        self.music_directory_chooser_popup = None

        self.song = None
        self.next_song = None

        self.edit_mode = False

    @staticmethod
    def format_time(seconds):
        """Formats time in MM:SS format."""
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02}:{seconds:02}"

    def select_song(self, selection, *args):
        """Handles file selection and play song immediately."""
        if not selection:
            print("No file selected.")
            return

        # Set song path and load it in the app
        filepath = selection if isinstance(selection, str) else selection[0]

        self.audio_player.load(filepath)
        self.song = Song(filepath)

        # Metadata set up
        self.ids.title_input.text = self.song.title
        self.ids.artist_input.text = self.song.artist
        self.ids.album_input.text = self.song.album
        self.ids.genre_input.text = self.song.genre
        self.ids.date_input.text = self.song.date
        self.ids.cover.source = self.song.cover
        self.ids.cover.reload()

        # Next song set up
        current_index = self.songs_list.index(filepath)
        self.next_song = Song(self.songs_list[current_index + 1])

        self.ids.next_song_filepath.text = os.path.basename(self.next_song.filepath)
        self.ids.next_song_title.text = self.next_song.title
        self.ids.next_song_artist.text = self.next_song.artist
        self.ids.next_song_cover.source = self.next_song.cover
        self.ids.next_song_cover.reload()

        # Set total duration of the song on the slider
        total_duration = self.song.duration
        self.ids.total_time_label.text = f"/ {self.format_time(total_duration)}"
        self.ids.progress_slider.max = total_duration
        self.play()

    def play(self):
        """Plays, pauses or resumes the selected song."""
        if not self.audio_player.current_song:
            print("No song selected.")
            return

        if not self.audio_player.is_playing:
            print(f"Playing: {self.audio_player.current_song}")
            self.audio_player.play()
            self.ids.title_status.text = f"Playing: {os.path.basename(self.audio_player.current_song)}"

            # Move slider cursor every sec
            Clock.schedule_interval(self.update_slider, 1)

        elif self.audio_player.is_playing:
            self.audio_player.pause()

            self.ids.title_status.text = f"Paused: {os.path.basename(self.audio_player.current_song)}"

    def next(self):
        print("Next song triggered")
        self.select_song(self.next_song.filepath)

    def update_slider(self, dt=None):
        """Update the slider and time labels to reflect the current play time."""
        if self.audio_player.current_song:
            current_time = int(self.audio_player.get_current_time())
            #print(f"Get Current time is {current_time} seconds")
            formatted_current_time = self.format_time(current_time)  # Convert to MM:SS format
            self.ids.progress_slider.value = current_time
            self.ids.current_time_label.text = formatted_current_time  # Update current time

    def seek_in_song(self, slider, touch):
        """Seeks to the chosen position in the song when the user moves the slider."""
        if touch.grab_current == slider or touch.grab_current is None:
            chosen_seconds = slider.value
            #print(f"Seeking to {chosen_seconds} seconds")
            self.audio_player.seek(chosen_seconds)  # Seek in the backend

            # Force UI update to match new position
            self.ids.current_time_label.text = self.format_time(chosen_seconds)
            self.ids.progress_slider.value = chosen_seconds

            if not self.audio_player.is_playing:  # Only restart updates if song was playing
                Clock.unschedule(self.update_slider)  # Prevent conflicts
                Clock.schedule_once(Clock.schedule_interval(self.update_slider, 1), 0.5)

    def metadata_edit(self):
        """Toggle metadata fields between editable and read-only mode."""
        if not self.edit_mode:
            self.edit_mode = True
            self.ids.edit_metadata.text = "Save"
            #self.enable_metadata_inputs(True)
        else:
            self.edit_mode = False
            self.ids.edit_metadata.text = "Edit Metadata"
            #self.enable_metadata_inputs(False)

            current_time = self.audio_player.get_current_time()
            self.audio_player.unload()

            self.song.save_metadata(self.get_metadata_inputs())

            self.audio_player = AudioPlayer()
            self.audio_player.load(self.song.filepath)
            self.audio_player.seek(current_time)
            self.audio_player.play()

    def get_metadata_inputs(self):
        """Retrieve edited metadata from text input fields."""
        return {
            "title": self.ids.title_input.text,
            "artist": self.ids.artist_input.text,
            "album": self.ids.album_input.text,
            "genre": self.ids.genre_input.text,
            "date": self.ids.date_input.text
        }

    def on_dropdown_settings_select(self, option):
        """Handles option selection"""
        print(f"Selected option: {option}")

        # Call appropriate function based on the selected option
        if option == "Browse":
            self.open_file_browser()
        elif option == "Cloud":
            self.download_music()
        elif option == "Upload":
            self.upload_music()
        elif option == "Search":
            self.search_music()

    def open_file_browser(self):
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
            self.list_files()

    def list_files(self):
        """Lists all audio files and allows the user to play the selected one."""
        if not os.path.isdir(self.music_directory):
            print(f"Invalid directory: {self.music_directory}")
            return

            # Supported audio file formats
        valid_extensions = {".mp3", ".wav", ".flac", ".ogg", ".m4a"}
        songfile_to_songpath = []
        # Walk through directories and collect files
        for root, _, files in os.walk(self.music_directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in valid_extensions):
                    song_path = os.path.join(root, file)
                    songfile_to_songpath.append({"filename": file, "path": song_path})
                    self.songs_list.append(song_path)

        self.number_of_songs = len(self.songs_list)

        # Update music_list (RecycleView)
        self.ids.music_list.data = [
            {
                "text": song["filename"],
                "on_release": partial(self.select_song, song["path"])
            }
            for song in songfile_to_songpath
        ]

        #print(f"Found {len(songs)} songs in {self.music_directory}")
        #print(f"Updated music_list with {len(self.ids.music_list.data)} items")


    def downloaderUI(self):
        print("Starting download process...")

    def syncUI(self):
        print("Opening upload window...")

    def searchUI(self):
        print("Opening search dialog...")


class PlayerApp(App):
    def build(self):
        return PlayerUI()

