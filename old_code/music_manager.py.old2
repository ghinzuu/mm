from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from frontend.player import PlayerUI


class MainAppLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.add_widget(PlayerUI())  # Adding the music player UI


class MainApp(App):
    def build(self):
        return MainAppLayout()


if __name__ == "__main__":
    MainApp().run()
