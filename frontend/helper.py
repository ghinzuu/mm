
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.progressbar import ProgressBar
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.textinput import TextInput
from kivy.properties import NumericProperty, ListProperty
from kivy.animation import Animation
from kivy.app import App

PHONE_WIDTH = 720


def go_screen(screen_name, direction="left"):
    """
    Switches between the various screen of the app
    """
    app = App.get_running_app()
    screen_manager = app.root.ids.screen_manager
    screen_manager.transition.direction = direction
    screen_manager.current = screen_name


def apply_marquee(widget):
    label = widget.ids.scrolling_label

    def animate(*_):
        text_width = label.texture_size[0]  # true text width
        box_width = widget.width           # container width

        if text_width > box_width:
            distance = text_width + box_width
            duration = distance / widget.speed

            # Reset label to start position just outside the right
            label.x = box_width

            # Animate across
            anim = Animation(x=-text_width, duration=duration, t="linear")
            anim.bind(on_complete=lambda *_: animate())
            anim.start(label)
        else:
            # Keep text pinned left if it fits
            label.x = 10

    Clock.schedule_once(lambda *_: animate(), 0.2)


class ClickableBox(ButtonBehavior, BoxLayout):
    """A BoxLayout that behaves like a button."""
    pass


class ThemedTextInput(TextInput):
    underline_width = NumericProperty(0)
    underline_color = ListProperty([0.35, 0.70, 0.64, 1])

    def animate_underline(self, focused):
        if focused:
            Animation(underline_width=self.width, d=0.2, t="out_quad").start(self)
        else:
            Animation(underline_width=0, d=0.2, t="out_quad").start(self)

class LightButton(Button):
    pass


class ListLoaderPopup(Popup):
    """
    This class is used in the loader to generate a popup displaying dynamically all the files that
    are to be (down/up)loaded
    """
    def __init__(self, title="Loading list...", x=0.95, y=0.95, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.size_hint = (x, y)

        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        self.spinner = Image(
            source="frontend/img/loader/Settings.gif",
            anim_delay=0.05
        )
        layout.add_widget(self.spinner)

        self.content = layout

    def start_spinner(self):
        self.spinner.anim_delay = 0.05

    def stop_spinner(self):
        self.spinner.anim_delay = 0

    def populate(self, list, global_status, on_confirm, on_cancel=None, **kwargs):
        """
        Populates the popup loader with each song of in the playlist and 
        sets its buttons
        list: list of items [{"id": "...", "title": "...", "url": "..."}]
        on_confirm: callback(list_of_items) -> triggered when user confirms
        on_cancel: callback() -> optional, triggered on cancel
        """

        self.list = list
        #self.title = global_status
        self.title = "List loaded"
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.item_widgets = {}

        # --- Layout ---
        main_layout = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))

        # --- Custom title with global progress ---
        title_layout = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(50))
        self.title_label = Label(text=global_status, size_hint_y=None, height=dp(30))
        self.global_progress = ProgressBar(max=len(list), value=0, size_hint_y=None, height=dp(20))
        title_layout.add_widget(self.title_label)
        title_layout.add_widget(self.global_progress)
        main_layout.add_widget(title_layout)

        # --- Scrollable list ---
        scroll = ScrollView(size_hint=(1, 1))
        list_layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(5))
        list_layout.bind(minimum_height=list_layout.setter("height"))

        for item in list:
            row = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(60))

            # Handle dict (YouTube/SoundCloud) vs str (Google Drive filenames)
            if isinstance(item, dict):
                title = item.get("title", "Unknown")
                item_id = item.get("id", title)
            else:
                title = str(item)
                item_id = title  # use filename as unique ID

            label = Label(text=title, size_hint_y=None, height=dp(30))
            progress = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(20))

            row.add_widget(label)
            row.add_widget(progress)
            list_layout.add_widget(row)

            self.item_widgets[item_id] = {"label": label, "progress": progress}

        scroll.add_widget(list_layout)
        main_layout.add_widget(scroll)

        # --- Confirm / Cancel buttons ---
        self.button_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        self.confirm_btn = Button(text="Confirm", on_release=lambda x: self._confirm())
        self.cancel_btn = Button(text="Cancel", on_release=lambda x: self._cancel())
        self.button_layout.add_widget(self.confirm_btn)
        self.button_layout.add_widget(self.cancel_btn)
        main_layout.add_widget(self.button_layout)

        self.content = main_layout
    
    #
    # --- Public methods ---
    #
    def update_progress(self, item_id, value):
        """Update progress bar for given item (0-100)."""
        if item_id in self.item_widgets:
            Clock.schedule_once(lambda dt: setattr(self.item_widgets[item_id]["progress"], "value", value))

    def mark_done(self, item_id, success=True):
        """Mark item as finished (green if success, red if fail)."""
        if item_id in self.item_widgets:
            label = self.item_widgets[item_id]["label"]
            color = (0, 1, 0, 1) if success else (1, 0, 0, 1)
            Clock.schedule_once(lambda dt: setattr(label, "color", color))

    def update_title(self, item_id, new_title):
        """Update the label of a specific item in the scrollable list."""
        if item_id in self.item_widgets:
            label = self.item_widgets[item_id]["label"]
            Clock.schedule_once(lambda dt: setattr(label, "text", new_title))

    
    def complete_button(self):
        """Call this when all downloads are finished"""
        # Clear current buttons layout
        self.button_layout.clear_widgets()

        # Add single "Download Complete" button
        complete_btn = Button(text="Download Complete", size_hint_y=None, height=dp(50))
        complete_btn.bind(on_release=lambda x: self.dismiss())
        self.button_layout.add_widget(complete_btn)

    #
    # --- Internal ---
    #
    def _confirm(self):
        # Disable buttons to prevent double clicks
        self.confirm_btn.disabled = True
        self.cancel_btn.disabled = True
        # Calls the on_confirm implementation in loader.py
        if self.on_confirm:
            self.on_confirm(self.list)
        
    def _cancel(self):
        if self.on_cancel:
            self.on_cancel()
        self.dismiss()
