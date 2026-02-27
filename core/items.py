import arcade
import random


class DroppedItem(arcade.Sprite):
    """Класс для выброшенных ресурсов"""

    def __init__(self, texture, item_type, x, y):
        super().__init__(texture)
        self.item_type = item_type
        self.center_x = x
        self.center_y = y

        self.change_y = random.uniform(2, 5)
        self.change_x = random.uniform(-2, 2)

        self.is_thrown = False
        self.timer = 0.0