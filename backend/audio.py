import pygame
from mutagen.mp3 import MP3


class AudioPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.current_song = None
        self.is_playing = False
        self.marked_time = 0

    def load(self, file_path=None):
        #print(f"Loading file: {file_path}")
        self.marked_time = 0
        pygame.mixer.music.stop()  # Ensure the previous song is stopped
        pygame.mixer.music.load(file_path)
        self.current_song = file_path
        self.is_playing = False  # Reset play state

    def play(self):
        """Plays a new song or resumes a paused song."""
        #print(f"play-status? {self.is_playing}")
        #print(f"play-current_time? {self.get_current_time()}")
        if self.current_song and not self.is_playing:  # play song
            pygame.mixer.music.play(start=float(self.get_current_time()))
        self.is_playing = True

    def pause(self):
        if pygame.mixer.music.get_busy():
            self.marked_time = self.get_current_time()
            #print(f"pause-marked_time? {self.marked_time}")
            pygame.mixer.music.pause()
            self.is_playing = False

    def stop(self):
        pygame.mixer.music.stop()
        self.current_song = None
        self.is_playing = True

    def seek(self, seconds):
        """Seeks to a specific time in the song."""
        if self.current_song:
            #print(f"position? {seconds}")
            #print(f"seek-status? {self.is_playing}")  # Debugging
            try:
                self.marked_time = seconds
                if self.is_playing:  # Only reload if the song is playing
                    pygame.mixer.music.stop()
                    pygame.mixer.music.load(self.current_song)
                    pygame.mixer.music.play(start=float(seconds))  # Restart at new position
            except TypeError:
                print("Error: seek() received incorrect input type.")

    def get_duration(self, file_path):
        audio = MP3(file_path)
        return audio.info.length  # Duration in seconds

    def format_time(self, seconds):
        """Format seconds into a MM:SS format."""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02}:{seconds:02}"

    def get_current_time(self):
        """
        Returns the current time of the audio in seconds.
        We need to track time throughout the song. get_pos tracks the number of seconds since marked time.
        Each time the song is paused get_pos is reinitialized to 0, so marked time has to store the last value
        current time was. Current time always is marked time + get_pos
        """
        #print(f"get_current_time-marked_time? {self.marked_time}")
        #print(f"get_current_time-get_pos? {pygame.mixer.music.get_pos() / 1000}")
        if not pygame.mixer.music.get_busy():
            return self.marked_time  # If not playing, return last marked time
        return self.marked_time + (pygame.mixer.music.get_pos() / 1000)  # Add elapsed time to the marked time

