import arcade
import arcade.gui
import os
import glob
from .game import GameView
from .constants import *


class MainMenu(arcade.View):
    """Вид (Экран) Главного меню игры"""

    def __init__(self):
        super().__init__()
        self.manager = arcade.gui.UIManager()
        self.v_box = arcade.gui.UIBoxLayout(space_between=20)

        new_game_button = arcade.gui.UIFlatButton(text="Новая игра", width=300)
        self.v_box.add(new_game_button)
        new_game_button.on_click = self.on_click_new_game

        load_game_button = arcade.gui.UIFlatButton(text="Продолжить", width=300)
        self.v_box.add(load_game_button)
        load_game_button.on_click = self.on_click_load_game

        settings_button = arcade.gui.UIFlatButton(text="Полноэкранный режим", width=300)
        self.v_box.add(settings_button)
        settings_button.on_click = self.on_click_settings

        quit_button = arcade.gui.UIFlatButton(text="Выйти", width=300)
        self.v_box.add(quit_button)
        quit_button.on_click = self.on_click_quit

        anchor = arcade.gui.UIAnchorLayout()
        anchor.add(child=self.v_box, anchor_x="center_x", anchor_y="center_y")
        self.manager.add(anchor)

        self.title_text = arcade.Text(
            text="QUANTUM RIFT",
            x=SCREEN_WIDTH / 2,
            y=SCREEN_HEIGHT - 150,
            color=arcade.color.CYAN,
            font_size=60,
            anchor_x="center",
            bold=True
        )

    def on_click_new_game(self, event):
        """Очистка сохранений и запуск новой игры"""
        if os.path.exists("saves"):
            for f in glob.glob("saves/*.json"):
                try:
                    os.remove(f)
                except Exception as e:
                    print(f"Ошибка удаления файла {f}: {e}")

        game_view = GameView()
        game_view.setup()
        self.window.show_view(game_view)

    def on_click_load_game(self, event):
        """Запуск игры без очистки сохранений"""
        game_view = GameView()
        game_view.setup()
        self.window.show_view(game_view)

    def on_click_settings(self, event):
        self.window.set_fullscreen(not self.window.fullscreen)

    def on_click_quit(self, event):
        arcade.exit()

    def on_draw(self):
        self.clear()
        self.manager.draw()

        window = arcade.get_window()
        self.title_text.x = window.width / 2
        self.title_text.y = window.height - 150
        self.title_text.draw()

    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK)
        self.manager.enable()

    def on_hide_view(self):
        self.manager.disable()