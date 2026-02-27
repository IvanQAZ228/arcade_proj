import arcade
from .constants import *
from .ui_slot import UISlot


class UIHotbarSlots:
    def __init__(self, slot_count, spacing, bg_texture):
        self.slot_count = slot_count
        self.spacing = spacing
        self.slots = [UISlot(bg_texture) for _ in range(slot_count)]

    @property
    def width(self):
        return self.slot_count * UI_SLOT_SIZE + (self.slot_count - 1) * self.spacing

    def draw(self, start_x, y, player_inventory, selected_index, slot_contents, item_textures):
        for i, slot in enumerate(self.slots):
            x = start_x + i * (UI_SLOT_SIZE + self.spacing)
            item_type = slot_contents[i]
            item_tex = None
            count = 0

            if item_type:
                item_tex = item_textures.get(item_type)
                count = player_inventory.get(item_type, 0)

            slot.draw(x, y, UI_SLOT_SIZE, item_tex, count, is_selected=(i == selected_index))