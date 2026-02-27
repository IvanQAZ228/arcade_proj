import arcade


class UISlot:
    """Класс отдельной ячейки инвентаря"""

    def __init__(self, bg_texture):
        self.bg_texture = bg_texture

        self.count_text = arcade.Text(
            text="",
            x=0,
            y=0,
            color=arcade.color.WHITE,
            font_size=14,
            bold=True,
            anchor_x="center",
            anchor_y="center",
            font_name=("Arial", "calibri")
        )

    def draw(self, x, y, size, item_texture, count, is_selected):
        arcade.draw_texture_rect(self.bg_texture, arcade.XYWH(x, y, size, size))

        color = arcade.color.WHITE if is_selected else arcade.color.DARK_GRAY
        thickness = 3 if is_selected else 1
        arcade.draw_rect_outline(arcade.XYWH(x, y, size, size), color, thickness)

        if item_texture and count > 0:
            arcade.draw_texture_rect(item_texture, arcade.XYWH(x, y, size, size))

            badge_radius = 12
            badge_x = x + size/2 - badge_radius - 4
            badge_y = y + badge_radius + 4

            arcade.draw_circle_filled(badge_x, badge_y, badge_radius, (20, 20, 20, 220))
            arcade.draw_circle_outline(badge_x, badge_y, badge_radius, arcade.color.GRAY, 1)

            self.count_text.text = str(count)
            self.count_text.x = badge_x
            self.count_text.y = badge_y
            self.count_text.draw()