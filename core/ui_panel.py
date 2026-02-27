import arcade
from .constants import *
from .ui_hotbar import UIHotbarSlots
from .ui_energy import UIEnergyBar
from .ui_hp import UIHpBar


class UIMainPanel:
    def __init__(self, tex_ui_slot, tex_energy_bg, tex_energy_fill, tex_hp_bg, tex_hp_fill):
        self.slots_panel = UIHotbarSlots(UI_HOTBAR_SLOTS, UI_SLOT_SPACING, tex_ui_slot)
        self.energy_bar = UIEnergyBar(tex_energy_bg, tex_energy_fill)
        self.hp_bar = UIHpBar(tex_hp_bg, tex_hp_fill)

    def draw(self, player, selected_slot_index, slot_contents, item_textures):
        window = arcade.get_window()
        screen_width = window.width

        y_pos = 40
        bar_w = 200
        bar_h = 24
        spacing_between = 10

        total_width = self.slots_panel.width + spacing_between + bar_w
        start_x = (screen_width - total_width) / 2

        self.slots_panel.draw(start_x, y_pos, player.inventory, selected_slot_index, slot_contents, item_textures)

        energy_x = start_x + self.slots_panel.width + spacing_between - 16
        energy_y = y_pos + UI_SLOT_SIZE - bar_h - 32
        self.energy_bar.draw(energy_x, energy_y, bar_w, bar_h, player.mana, player.max_mana)

        hp_y = energy_y - bar_h - 5
        self.hp_bar.draw(energy_x, hp_y, bar_w, bar_h, player.hp, player.max_hp)