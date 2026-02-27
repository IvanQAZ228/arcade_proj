import arcade


class UIHpBar:
    """Класс шкалы HP"""

    def __init__(self, bg_texture, fill_texture):
        self.bg_texture = bg_texture
        self.fill_texture = fill_texture

    def draw(self, x, y, width, height, current_mana, max_mana):
        arcade.draw_texture_rect(self.bg_texture, arcade.LRBT(x, x + width, y, y + height))

        mana_percent = max(0.0, min(1.0, current_mana / max_mana))
        fill_w = int(width * mana_percent)

        if fill_w > 0:
            cropped = self.fill_texture.crop(0, 0, fill_w, height)

            arcade.draw_texture_rect(cropped, arcade.LRBT(x, x + fill_w, y, y + height))