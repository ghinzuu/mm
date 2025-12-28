import os
from threading import Thread
from pathlib import Path

# kivy imports
from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.properties import StringProperty

import backend.controller.file_system_manager as fsm
import backend.controller.download_manager as dlm
import backend.controller.cloud_manager as clm
import frontend.helper as helper

kv_path = os.path.join(os.path.dirname(__file__), "kivy", "loader_pc_ui.kv")
if Window.width <= helper.PHONE_WIDTH:  # phone layout
    kv_path = os.path.join(os.path.dirname(__file__), "kivy", "loader_phone_ui.kv")
Builder.load_file(kv_path)


class LoaderUI(Screen):

    sync_mode = StringProperty("pc_to_phone")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.download_directory = fsm.load_config("download_directory") or os.getcwd()
        self.favourite_dl_directory = fsm.load_config("favourite_dl_directory") or "browser favourite folder name"
        self.dl_directory_chooser_popup = None
        self.download_url_popup = None
        self.download_url_progress = None
        self.download_url_button = None

        self.google_drive = clm.GoogleDriveApi()

    def on_kv_post(self, base_widget):
        self.ids.dl_dir_path.text = self.download_directory
        self.ids.favourite_dl_directory.text = self.favourite_dl_directory
        self.download_url_button = self.ids.download_url_button
        
    def go_playerUI(self):
        print("Switching to Player screen...")
        helper.go_screen("player", direction="right")

    #
    # --- Section 1: MP3 download ---
    #
    
    # --> Browse Second button
    def open_file_browser(self):
        """Creates and opens the file chooser popup dynamically"""
        print("Opening file browser for loader...")

        # Create file chooser
        filechooser = FileChooserListView(path="D:/", dirselect=True)

        # Create the "Select" button
        select_button = Button(text="Select", size_hint_y=None, height=50)
        select_button.bind(on_release=lambda instance: self.select_dl_directory(filechooser))

        # Layout for the popup
        layout = BoxLayout(orientation="vertical", spacing=10)
        layout.add_widget(filechooser)
        layout.add_widget(select_button)

        # Create the popup
        self.dl_directory_chooser_popup = Popup(
            title="Select download target directory",
            content=layout,
            size_hint=(0.9, 0.9),
            auto_dismiss=False
        )
        self.dl_directory_chooser_popup.open()


    def select_dl_directory(self, filechooser):
        """Selects the chosen directory and saves it."""
        if filechooser.selection:
            self.download_directory = filechooser.selection[0]
            print(f"Selected directory: {self.download_directory}")
            fsm.save_config("download_directory", self.download_directory)
            self.dl_directory_chooser_popup.dismiss()
            self.ids.target_dl_dir_path.text = self.download_directory

    # --> Loading progress bar functions
    def update_progress(self, percent):
        # Called from background thread, must schedule on main thread
        Clock.schedule_once(lambda dt: self._set_progress(percent))

    def _set_progress(self, percent):
        if self.download_url_progress:
            self.download_url_progress.value = percent

    def download_complete(self):
        Clock.schedule_once(lambda dt: self._finish_download())

    def _finish_download(self):
        self.google_drive.upload_file(self.google_drive.sync_id, "cloud_inventory.json", overwrite=True)
        self.google_drive.music_manager_list = None # list needs to be refreshed with new/deleted files

        if self.download_url_popup:
            self.download_url_popup.dismiss()
            self.download_url_popup = None
        if self.download_url_button:
            self.download_url_button.disabled = False

    def download_finished(self):
        Clock.schedule_once(lambda dt: self._finish_download())

    def update_title(self, song_name):
        Clock.schedule_once(lambda dt: setattr(self.download_url_popup, "title", f"Downloading {song_name}..."))

    def list_loader(self, song_list, action="download"):
        """
        Download/Upload a list of URLs with a popup showing per-song progress and global progress.
        song_list: list of dicts: [{"id": "...", "title": "...", "url": "..."}] when youtube or soundcloud
        platform: used in the popup title
        """
        platform = "Google Drive"
        if song_list and isinstance(song_list[0], dict) and "url" in song_list[0]:
            if "youtube" in song_list[0]["url"]:
                platform = "Youtube"
            elif "soundcloud" in song_list[0]["url"]:
                platform = "SoundCloud" 
        
        number_of_songs = len(song_list)
        global_status = f"Downloaded 0/{number_of_songs} songs from {platform} into {self.download_directory}"
        if action == "upload":
            global_status = f"Uploaded 0/{number_of_songs} songs from {self.download_directory} into Google Drive's music_manager directory"
        
        # Create and open the popup immediately
        popup_loader = helper.ListLoaderPopup()
        popup_loader.open()

        # Called when Confirm is pressed
        def on_confirm(list_to_load):
            # Capture current download directory
            self.download_directory = self.ids.dl_dir_path.text

            remaining = number_of_songs
            completed = 0

            # Called for each song when download finishes
            def song_done(item_id, success=True):
                nonlocal remaining, completed
                completed += 1
                remaining -= 1

                # Update per-song progress
                popup_loader.mark_done(item_id, success)

                # Update global progress bar
                Clock.schedule_once(lambda dt: setattr(popup_loader.global_progress, "value", completed))

                # Update title with count
                new_title = f"Downloaded {completed}/{number_of_songs} songs from {platform} into {self.download_directory}"
                if action == "upload":
                    new_title = f"Uploaded {completed}/{number_of_songs} songs from {self.download_directory} into Google Drive's music_manager directory"
                Clock.schedule_once(lambda dt: setattr(popup_loader.title_label, "text", new_title))

                # When all done (dl/uploads) : upload updated cloud inventory / auto sync / show complete button 
                if remaining <= 0:
                    # Upload cloud_inventory.json once all songs are dl/upload
                    if platform == "Google Drive":
                        self.google_drive.upload_file(self.google_drive.sync_id, "cloud_inventory.json", overwrite=True)
                        Clock.schedule_once(lambda dt: self.syncUI())

                    Clock.schedule_once(lambda dt: popup_loader.complete_button())

            # Start all loads
            for item in list_to_load:
                if platform == "Youtube" or platform == "SoundCloud":
                    item_id = item["id"]  # capture current ID
                    dlm.dl_url_to_mp3(
                        item["url"],
                        self.download_directory,
                        progress_callback=lambda val, i=item_id: popup_loader.update_progress(i, val),
                        done_callback=lambda success=True, i=item_id: song_done(i, success),
                        title_callback=lambda t, i=item_id: popup_loader.update_title(i, t)
                    )
                elif platform == "Google Drive":
                    item_id = os.path.basename(item)
                    if action == "download":
                        self.google_drive.download_mp3(
                            item, 
                            self.download_directory,
                            progress_callback=lambda val, i=item_id: popup_loader.update_progress(i, val),
                            done_callback=lambda success=True, i=item_id: song_done(i, success),
                            title_callback=lambda t, i=item_id: popup_loader.update_title(i, t)                        
                        )
                    elif action == "upload":
                        self.google_drive.upload_mp3(
                            Path(self.download_directory) / item,
                            progress_callback=lambda val, i=item_id: popup_loader.update_progress(i, val),
                            done_callback=lambda success=True, i=item_id: song_done(i, success),
                            title_callback=lambda t, i=item_id: popup_loader.update_title(i, t)
                        )

        # Populate the popup with the url dictionary
        popup_loader.populate(song_list, global_status, on_confirm)

    # --> Download first button
    def download_url(self, url: str):
        if not url.strip():
            return

        if "youtube" in url and "list" in url:
            url_list = dlm.list_youtube_playlist(url)
            self.list_loader(url_list)  

        else:
            self.download_url_progress = ProgressBar(max=100, value=0)
            layout = BoxLayout(orientation="vertical", spacing=10)
            layout.add_widget(self.download_url_progress)

            self.download_url_popup = Popup(
                title="Downloading...",
                content=layout,
                size_hint=(0.6, 0.2),
                auto_dismiss=False
            )
            self.download_url_popup.open()
            self.ids.download_url_button.disabled = True

            dlm.dl_url_to_mp3(
                url,
                self.download_directory,
                progress_callback=self.update_progress,
                done_callback=self.download_finished,
                title_callback=self.update_title
            )

    # --> Download third button 
    def download_favourite(self, folder: str):

        fsm.save_config("favourite_dl_directory", folder)
        self.favourite_directory = folder

        # Get the selected browser
        selected_browser = None
        for child in self.ids.browser_box.children:
            if child.state == "down":
                selected_browser = child.text.lower()  # e.g., "chrome", "brave", "firefox", "edge"
                break

        if not selected_browser:
            print("[LoaderUI] No browser selected")
            return

        print(f"[LoaderUI] Download requested from favorite folder: {folder} in {selected_browser}")

        paths = fsm.get_default_urls_paths()
        browser_key = f"{selected_browser}_bookmarks"
        if browser_key not in paths:
            print(f"[LoaderUI] Bookmarks path for {selected_browser} not found")
            return

        try:
            urls, urls_names = fsm.get_urls(paths[browser_key], folder, browser=selected_browser)
            if urls:
                url_list = [{"url": url, "title": urls_names[url], "id": url} for url in urls]
                self.list_loader(url_list)
            else:
                print(f"[LoaderUI] No bookmarks found in folder '{folder}' for {selected_browser}")
        except Exception as e:
            print(f"[LoaderUI] Could not read bookmarks from {selected_browser}: {e}")

        
    #
    # --- Section 2: Sync status ---
    #
    def syncUI(self):
        """
        Populate upload and download box with a label stating amount of transfer to do
        Put in app memory songs to upload/download to/from cloud  
        #print("self.to_upload:", self.to_upload)
        #print("self.to_download:", self.to_download)                          
        """
        print(f"[LoaderUI] Sync button clicked, mode={self.sync_mode}")
        
        sync_popup = helper.ListLoaderPopup("Synchronizing local with remote device and google drive...", 0.4, 0.4)
        sync_popup.open()

        def do_sync():
            self.to_upload, self.to_download = self.google_drive.sync(
                self.download_directory,
                mode=str(self.sync_mode),
            )

            # update UI back on main thread
            def update_ui(dt):
                self.ids.upload_count.text = f"{len(self.to_upload)} songs to upload"
                self.ids.download_count.text = f"{len(self.to_download)} songs to download"
                self.ids.upload_count.opacity = 1
                self.ids.download_count.opacity = 1
                self.ids.upload_btn.disabled = False
                self.ids.download_btn.disabled = False
                sync_popup.dismiss()

            Clock.schedule_once(update_ui)

        # run sync in background
        Thread(target=do_sync).start()

                 
    #
    # --- Section 3: Cloud ---
    #
    def cloud_upload(self):
        """Triggered when user clicks the left side (upload)."""
        if not hasattr(self, "to_upload") or not self.to_upload:
            print("[LoaderUI] No files to upload")
            return
        print(f"[LoaderUI] Upload triggered with {len(self.to_upload)} files")
        self.list_loader(self.to_upload, action="upload")
        

    def cloud_download(self):
        """Triggered when user clicks the right side (download)."""
        if not hasattr(self, "to_download") or not self.to_download:
            print("[LoaderUI] No files to download")
            return
        print(f"[LoaderUI] Download triggered with {len(self.to_download)} files")
        self.list_loader(self.to_download, action="download")
        
