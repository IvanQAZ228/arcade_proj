import arcade
import arcade.hitbox
import math
from .constants import *
from .world import get_texture


class Player(arcade.Sprite):
    def __init__(self):
        super().__init__()

        base_texture = get_texture("assets/textures/player.png", COLOR_PLAYER)
        self.tex_right = base_texture
        self.tex_left = base_texture.flip_horizontally()

        self.texture = self.tex_right
        self.facing_right = True

        self.hit_box = arcade.hitbox.HitBox(points=[
            (-24, -24),
            (24, -24),
            (24, 24),
            (-24, 24)
        ])

        self.start_x = 0
        self.start_y = 6 * SPRITE_PIXEL_SIZE

        self.change_x = 0
        self.change_y = 0
        self.left_pressed = False
        self.right_pressed = False

        self.mana = MAX_MANA
        self.max_mana = MAX_MANA

        self.hp = MAX_HP
        self.max_hp = MAX_HP

        self.dash_timer = 0.0

        self.on_biomass = False

        # Инвентарь
        self.inventory = {
            "dust": 0, "shard": 0, "scrap": 0, "metal_block": 0, "metal2_block": 0,
            "copper_ore": 0, "copper": 0, "copper_ingot": 0, "furnace": 0, "assembler": 0,
            "pickaxe": 0, "energy_dust": 0,
            "titanium_ore": 0, "titanium_ingot": 0, "uranium_ore": 0, "uranium_rod": 0,
            "spore": 0, "acid_flask": 0, "quantum_drill": 0, "titanium_block": 0, "glass_block": 0,
            "chem_lab": 0, "battery": 0, "reflector": 0, "terminal": 0
        }
        self.respawn()

    def respawn(self):
        self.center_x = self.start_x
        self.center_y = self.start_y
        self.change_x = 0
        self.change_y = 0
        self.mana = self.max_mana
        self.hp = self.max_hp
        self.dash_timer = 0.0

    def update_movement(self):
        if self.dash_timer > 0:
            self.change_x *= 0.95
            return

        self.change_x = 0
        speed = PLAYER_MOVEMENT_SPEED

        if self.on_biomass:
            speed *= 0.5

        if self.left_pressed and not self.right_pressed:
            self.change_x = -speed
        elif self.right_pressed and not self.left_pressed:
            self.change_x = speed

    def apply_impulse(self, target_x, target_y, multiplier=1.0):
        if self.on_biomass:
            return

        dy = target_y - self.center_y
        dx = target_x - self.center_x
        angle = math.atan2(dy, dx)

        self.change_x = math.cos(angle) * (IMPULSE_STRENGTH * multiplier)
        self.change_y = math.sin(angle) * (IMPULSE_STRENGTH * multiplier)

        self.dash_timer = 0.3 * multiplier

    def update(self, delta_time: float = 1 / 60):
        if self.dash_timer > 0:
            self.dash_timer -= delta_time

        if self.change_y > PLAYER_MAX_SPEED_Y:
            self.change_y = PLAYER_MAX_SPEED_Y
        elif self.change_y < -PLAYER_MAX_SPEED_Y:
            self.change_y = -PLAYER_MAX_SPEED_Y