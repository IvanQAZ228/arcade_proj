import arcade
from .constants import *
from .ui_panel import UIMainPanel


class GameUI:
    def __init__(self, tex_ui_slot, item_textures):
        self.camera = arcade.camera.Camera2D()
        self.item_textures = item_textures

        from .world import get_texture
        tex_energy_bg = get_texture("assets/textures/ui_energy_bg.png", arcade.color.DARK_GRAY, size=200)
        tex_energy_fill = get_texture("assets/textures/ui_energy_fill.png", arcade.color.BLUE, size=200)

        tex_hp_bg = get_texture("assets/textures/ui_hp_bg.png", arcade.color.DARK_GRAY, size=200)
        tex_hp_fill = get_texture("assets/textures/ui_hp_fill.png", arcade.color.RED, size=200)

        self.main_panel = UIMainPanel(tex_ui_slot, tex_energy_bg, tex_energy_fill, tex_hp_bg, tex_hp_fill)

        self.hint_text = arcade.Text(
            text="[E] Взаимодействовать",
            x=0, y=0, color=arcade.color.WHITE, font_size=16, anchor_x="center"
        )
        self.menu_text = arcade.Text(
            text="",
            x=0, y=0, color=arcade.color.CYAN, font_size=20, anchor_x="center", multiline=True, width=500,
            align="center"
        )

    def draw(self, player, selected_slot_index, slot_contents, show_interact_hint, show_teleport_menu):
        window = arcade.get_window()
        self.camera.position = (window.width / 2, window.height / 2)
        self.camera.use()

        self.main_panel.draw(player, selected_slot_index, slot_contents, self.item_textures)

        if show_teleport_menu:
            arcade.draw_rect_filled(arcade.XYWH(window.width / 2, window.height / 2, window.width, window.height),
                                    (0, 0, 0, 200))
            self.menu_text.x = window.width // 2
            self.menu_text.y = window.height // 2
            self.menu_text.draw()
        elif show_interact_hint:
            self.hint_text.x = window.width // 2
            self.hint_text.y = window.height // 2 - 100
            self.hint_text.draw()