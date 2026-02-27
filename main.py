import arcade
from core.constants import SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE
from core.menu import MainMenu
from core.music import MusicManager


class GameWindow(arcade.Window):
    """Кастомное окно игры для глобального управления музыкой"""

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable=True)

        self.music_manager = MusicManager("assets/music")
        self.music_manager.play_next()

    def on_update(self, delta_time):
        self.music_manager.update(delta_time)

        super().on_update(delta_time)


def main():
    window = GameWindow()

    menu_view = MainMenu()
    window.show_view(menu_view)

    arcade.run()


if __name__ == "__main__":
    main()