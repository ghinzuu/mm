import os
import threading
import time
import gc
import pygame


class AudioPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.current_song = None
        self.is_playing = False
        self.marked_time = 0
        self._current_time = 0
        self._tracking = False
        self._thread = None


    def load(self, file_path=None):
        #print(f"Loading file: {file_path}")
        self.marked_time = 0
        self._current_time = 0
        pygame.mixer.music.stop()  # Ensure the previous song is stopped
        pygame.mixer.music.load(file_path)
        self.current_song = file_path
        self.is_playing = False  # Reset play state

    def play(self):
        """Plays a new song or resumes a paused song."""
        print(f"play-status? {self.is_playing}")
        #print(f"play-current_time? {self.get_current_time()}")
        if self.current_song and not self.is_playing:  # play song
            pygame.mixer.music.play(start=float(self.get_current_time()))
            self.start_time_tracking()
        self.is_playing = True

    def pause(self):
        if pygame.mixer.music.get_busy():
            self.marked_time = self.get_current_time()
            #print(f"pause-marked_time? {self.marked_time}")
            pygame.mixer.music.pause()
            self.stop_time_tracking()
            self.is_playing = False

    def stop(self):
        pygame.mixer.music.stop()
        self.stop_time_tracking()
        self.current_song = None
        self.is_playing = False


    '''
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
    '''
    import os

    def seek(self, seconds):
        """Seeks to a specific time in the song with format-aware logic."""
        if self.current_song:
            try:
                seconds = max(0, min(seconds, getattr(self, "song_duration", seconds)))  # clamp

                ext = os.path.splitext(self.current_song)[1].lower()
                print("ext:" + ext)
                if ext in [".mp3", ".ogg"]:  
                    # Fast, non-blocking seek
                    self.marked_time = seconds
                    if self.is_playing:
                        pygame.mixer.music.set_pos(float(seconds))
                    else:
                        self.marked_time = seconds

                else:  
                    # WAV, FLAC, etc. → fallback to reload
                    self.marked_time = seconds
                    if self.is_playing:
                        pygame.mixer.music.stop()
                        pygame.mixer.music.load(self.current_song)
                        pygame.mixer.music.play(start=float(seconds))


                print("current time:" + str(self._current_time))

            except Exception as e:
                print(f"Seek failed: {e}")

    '''
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
    '''

    def start_time_tracking(self):
        self._tracking = True
        self._thread = threading.Thread(target=self._update_time, daemon=True)
        self._thread.start()

    def stop_time_tracking(self):
        self._tracking = False

    def _update_time(self):
        while self._tracking:
            if pygame.mixer.music.get_busy():
                self._current_time = self.marked_time + (pygame.mixer.music.get_pos() / 1000)
            time.sleep(0.2)  # update 5x per second

    def get_current_time(self):
        return self._current_time
    
    def unload(self):
        """Ensure the file is completely released."""
        if self.current_song:
            self.stop()
            self.current_song = None
            self.marked_time = None
            pygame.mixer.quit()  # This is what actually unloads the file



