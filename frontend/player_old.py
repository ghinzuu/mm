import os
from functools import partial
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from backend.file_system_manager import load_config, save_config
from backend.audio import AudioPlayer


class PlayerUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=10, spacing=10, **kwargs)

        # Instantiate audio player
        self.audio_player = AudioPlayer()

        # General variables used by player
        self.music_directory = load_config("music_directory") or os.getcwd()
        self.current_song = None
        self.is_playing = False
        self.total_duration = 0
        self.current_position = 0
        print(f"Selected directory: {self.music_directory}")

        # Song title
        self.song_label = Label(text="Song Title", font_size=24, size_hint_y=None, height=50)
        self.add_widget(self.song_label)

        # Progress bar slider
        self.progress_slider = Slider(min=0, max=100, value=0, step=1)
        self.progress_slider.bind(on_touch_up=self.seek_song)
        self.add_widget(self.progress_slider)

        # Control buttons layout
        button_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        self.play_button = Button(text="Play", on_release=self.play)
        self.pause_button = Button(text="Pause", on_release=self.pause)
        self.stop_button = Button(text="Stop", on_release=self.stop)

        button_layout.add_widget(self.play_button)
        button_layout.add_widget(self.pause_button)
        button_layout.add_widget(self.stop_button)
        self.add_widget(button_layout)

        # Settings dropdown menu
        self.settings_button = Button(text="Settings")
        self.dropdown = DropDown()

        path_button = Button(text="Path", size_hint_y=None, height=40)
        path_button.bind(on_release=lambda btn: self.open_file_chooser())
        self.dropdown.add_widget(path_button)

        for option in ["Download", "Upload"]:
            btn = Button(text=option, size_hint_y=None, height=40)
            btn.bind(on_release=lambda btn: self.dropdown.select(btn.text))
            self.dropdown.add_widget(btn)

        self.settings_button.bind(on_release=self.dropdown.open)
        self.add_widget(self.settings_button)

        # File list container
        self.file_list_container = ScrollView(size_hint=(1, 1))
        self.list_files()
        self.add_widget(self.file_list_container)

    def open_file_chooser(self):
        content = BoxLayout(orientation='vertical')
        filechooser = FileChooserListView(path="D:\\", dirselect=True)
        select_button = Button(text="Select", size_hint_y=None, height=50)

        # Bind the file chooser selection to the select_file method
        filechooser.bind(on_selection=self.select_file)

        def select_path(instance):
            if filechooser.selection:
                self.music_directory = filechooser.selection[0]
                print(f"Selected directory: {self.music_directory}")
                save_config("music_directory", self.music_directory)
                popup.dismiss()
                self.list_files()  # Refresh the file list

        select_button.bind(on_release=select_path)
        content.add_widget(filechooser)
        content.add_widget(select_button)

        popup = Popup(title="Select Music Directory", content=content, size_hint=(0.9, 0.9))
        popup.open()

    def list_files(self):
        """Lists all audio files and allows the user to select one."""
        allowed_extensions = ('.mp3', '.wav', '.flac', '.ogg', '.m4a')

        file_layout = GridLayout(cols=3, spacing=5, size_hint_y=None)
        file_layout.bind(minimum_height=file_layout.setter('height'))

        for root, _, files in os.walk(self.music_directory):
            for file in files:
                if file.lower().endswith(allowed_extensions):
                    file_path = os.path.join(root, file)
                    # Get the duration of the file
                    duration = self.audio_player.get_duration(file_path)
                    btn = Button(text=os.path.basename(file_path), size_hint_y=None, height=40)
                    # Add a label for the duration
                    duration_label = Label(text=self.audio_player.format_duration(duration), size_hint_x=None, width=100)
                    file_layout.add_widget(btn)
                    file_layout.add_widget(duration_label)
                    # Bind button to select the file
                    btn.bind(on_release=partial(self.select_file, file_path))

        self.file_list_container.clear_widgets()
        self.file_list_container.add_widget(file_layout)

    def select_file(self, file_path, *args):
        """Handles file selection and play song immediately."""
        if not file_path:
            print("No file selected.")
            return

        self.current_song = file_path  # Store the selected song
        self.audio_player.load(self.current_song)
        print(f"Selected file: {self.current_song}")

        # Check if the selected file is valid before playing
        if not os.path.isfile(self.current_song):
            print(f"Error: {self.current_song} is not a valid file.")
            return

        self.play()  # Automatically play the selected file

    def play(self, instance=None):
        """Plays or resumes the selected song."""
        if not self.current_song:
            print("No song selected.")
            return

        print(f"Playing: {self.current_song}")
        self.audio_player.play()  # Play the current song
        self.is_playing = True
        self.song_label.text = f"Now Playing: {os.path.basename(self.current_song)}"
        self.total_duration = self.audio_player.get_duration(self.current_song)
        self.progress_slider.max = self.total_duration
        self.update_slider()
        Clock.schedule_interval(self.update_slider, 1)

    def pause(self, instance=None):
        """Pause the current song."""
        self.audio_player.pause()
        self.is_playing = False
        self.song_label.text = "Paused"

    def stop(self, instance=None):
        """Stop the current song."""
        self.audio_player.stop()
        self.is_playing = False
        self.song_label.text = "No song playing"
        self.progress_slider.value = 0
        Clock.unschedule(self.update_slider)

    def update_slider(self, dt=None):
        """Update the slider to reflect the current play time."""
        if self.is_playing and self.current_song:
            # Get the current play time
            current_time = self.audio_player.get_current_time()
            self.progress_slider.value = current_time

    def seek_song(self, slider, touch):
        """Seeks to the chosen position in the song when the user moves the slider."""
        if touch.grab_current == slider:  # Ensure event belongs to the slider
            value = slider.value  # Get the actual slider value
            print(f"Seeking to {value} seconds")
            self.audio_player.seek(value)


class PlayerApp(App):
    def build(self):
        return PlayerUI()

