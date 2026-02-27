import arcade
import arcade.gui
import os
import math
import random
import json

from .constants import *
from .world import World, get_texture
from .player import Player
from .items import DroppedItem
from .ui import GameUI


class WalkingParticle(arcade.SpriteSolidColor):
    def __init__(self, x, y, color):
        super().__init__(4, 4, color)
        self.center_x = x
        self.center_y = y
        self.change_x = random.uniform(-1, 1)
        self.change_y = random.uniform(0.5, 2.5)
        self.alpha = 255
        self.fade_rate = random.uniform(10, 20)

    def update(self, delta_time: float = 1 / 60):
        self.center_x += self.change_x
        self.center_y += self.change_y
        self.change_y -= GRAVITY * 0.3
        self.alpha -= self.fade_rate
        if self.alpha <= 0:
            self.remove_from_sprite_lists()


class DamageText(arcade.Text):
    def __init__(self, text, x, y):
        super().__init__(text, x, y, arcade.color.RED, 16, bold=True)
        self.change_y = 1.0
        self.alpha = 255

    def update(self):
        self.y += self.change_y
        self.alpha -= 5
        if self.alpha <= 0: self.color = (0, 0, 0, 0)


class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        self.camera = arcade.camera.Camera2D()
        self.gui_camera = arcade.camera.Camera2D()
        self.window.ctx.enable(self.window.ctx.BLEND)
        self.init_shaders()

        self.time_elapsed = 0.0
        self.uranium_timer = 0.0
        self.max_depth = 0

        self.world = World()
        self.player = Player()
        self.player_list = arcade.SpriteList()
        self.items_list = arcade.SpriteList()
        self.particle_list = arcade.SpriteList()
        self.damage_texts = []
        self.physics_engine = None

        tex_ui_slot = get_texture("assets/textures/ui_slot.png", (30, 30, 30, 200), size=64)

        self.item_textures = {
            "dust": self.world.tex_item_dust,
            "energy_dust": self.world.tex_item_energy_dust,
            "shard": self.world.tex_item_shard,
            "scrap": self.world.tex_item_scrap,
            "metal2_block": self.world.tex_metal2,
            "copper_ore": self.world.tex_copper_ore,
            "copper": get_texture("assets/textures/item_copper.png", COLOR_COPPER_ITEM, 24),
            "copper_ingot": self.world.tex_item_copper_ingot,
            "furnace": self.world.tex_furnace,
            "assembler": self.world.tex_assembler,
            "teleporter": self.world.tex_teleporter,
            "extractor": self.world.tex_extractor,
            "press": self.world.tex_press,
            "pickaxe": get_texture("assets/textures/item_pickaxe.png", COLOR_PICKAXE, 48),
            "chest": self.world.tex_chest,

            "titanium_ore": self.world.tex_titanium_ore,
            "titanium_ingot": self.world.tex_item_titanium_ingot,
            "uranium_ore": self.world.tex_uranium_ore,
            "uranium_rod": self.world.tex_item_uranium_rod,
            "spore": self.world.tex_item_spore,
            "acid_flask": self.world.tex_item_acid_flask,
            "quantum_drill": self.world.tex_item_quantum_drill,
            "titanium_block": self.world.tex_titanium,
            "glass_block": self.world.tex_glass,
            "chem_lab": self.world.tex_chem_lab,
            "battery": self.world.tex_battery,
            "reflector": self.world.tex_reflector,
            "terminal": self.world.tex_terminal
        }

        self.ui = GameUI(tex_ui_slot, self.item_textures)
        self.ui.menu_text.text = "МЕНЮ ТЕЛЕПОРТАЦИИ\n\n[1] Телепорт на Базу (Алтарь)\n\nНажмите E или ESC/TAB чтобы закрыть"

        self.selected_slot_index = 0
        self.slot_contents = [None] * UI_HOTBAR_SLOTS

        self.show_interact_hint = False
        self.show_teleport_menu = False
        self.current_interactable = None
        self.hovered_block = None

        self.is_paused = False
        self.is_dead = False

        self.pause_manager = arcade.gui.UIManager()
        self.pause_v_box = arcade.gui.UIBoxLayout(space_between=20)
        btn_continue = arcade.gui.UIFlatButton(text="Продолжить", width=300)
        btn_continue.on_click = lambda e: self.toggle_pause()
        btn_save = arcade.gui.UIFlatButton(text="Сохранить", width=300)
        btn_save.on_click = lambda e: self.save_game()
        btn_exit = arcade.gui.UIFlatButton(text="Сохранить и выйти", width=300)
        btn_exit.on_click = self.on_exit
        self.pause_v_box.add(btn_continue)
        self.pause_v_box.add(btn_save)
        self.pause_v_box.add(btn_exit)
        self.pause_anchor = arcade.gui.UIAnchorLayout()
        self.pause_anchor.add(child=self.pause_v_box, anchor_x="center_x", anchor_y="center_y")
        self.pause_manager.add(self.pause_anchor)

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_manager.enable()
        else:
            self.pause_manager.disable()

    def on_exit(self, event):
        self.save_game()
        self.pause_manager.disable()
        from .menu import MainMenu
        self.window.show_view(MainMenu())

    def save_game(self):
        self.save_inventory()
        for chunk in self.world.active_chunks.values(): chunk.save()

    def init_shaders(self):
        self.program = None

    def save_inventory(self):
        os.makedirs("saves", exist_ok=True)
        with open("saves/player_inventory.json", "w") as f: json.dump(self.player.inventory, f)

    def load_inventory(self):
        if os.path.exists("saves/player_inventory.json"):
            with open("saves/player_inventory.json", "r") as f:
                saved_inv = json.load(f)
                for k, v in saved_inv.items(): self.player.inventory[k] = v
        self.update_hotbar()

    def add_to_inventory(self, item_type, amount=1):
        self.player.inventory[item_type] = self.player.inventory.get(item_type, 0) + amount
        self.save_inventory()
        self.update_hotbar()

    def remove_from_inventory(self, item_type, amount=1):
        if self.player.inventory.get(item_type, 0) >= amount:
            self.player.inventory[item_type] -= amount
            self.save_inventory()
            self.update_hotbar()
            return True
        return False

    def update_hotbar(self):
        for i in range(UI_HOTBAR_SLOTS):
            item = self.slot_contents[i]
            if item and self.player.inventory.get(item, 0) <= 0: self.slot_contents[i] = None

        for item, count in self.player.inventory.items():
            if count > 0 and item not in self.slot_contents:
                if None in self.slot_contents:
                    empty_idx = self.slot_contents.index(None)
                    self.slot_contents[empty_idx] = item

    def spawn_item(self, item_type, x, y, is_thrown=False, direction=1):
        tex = self.item_textures.get(item_type, self.world.tex_metal2)
        item = DroppedItem(tex, item_type, x, y)
        if is_thrown:
            item.is_thrown = True
            item.change_x = direction * 12
            item.change_y = 5
        self.items_list.append(item)

    def take_damage(self, amount):
        if self.is_dead: return
        self.player.hp -= amount
        self.damage_texts.append(DamageText(f"-{amount}", self.player.center_x, self.player.top + 10))
        if self.player.hp <= 0:
            self.player.hp = 0
            self.is_dead = True

    def process_assembler_craft(self, block):
        from collections import Counter
        loaded = Counter(getattr(block, 'items_loaded', []))

        recipes = {
            "pickaxe": {"copper_ingot": 3, "metal2_block": 2},
            "furnace": {"metal2_block": 8, "shard": 1},
            "teleporter": {"shard": 3, "copper_ingot": 2, "metal2_block": 5},
            "chest": {"metal2_block": 4, "copper_ingot": 2},
            "titanium_block": {"titanium_ingot": 2},
            "glass_block": {"dust": 4,"titanium_ingot": 1},
            "chem_lab": {"titanium_ingot": 3, "glass_block": 2},
            "battery": {"titanium_ingot": 4, "uranium_rod": 1},
            "reflector": {"titanium_ingot": 2, "shard": 2}
        }

        crafted = False
        for result, reqs in recipes.items():
            if len(loaded) == len(reqs) and all(loaded.get(k) == v for k, v in reqs.items()):
                self.spawn_item(result, block.center_x, block.center_y + SPRITE_PIXEL_SIZE)
                block.items_loaded.clear()
                crafted = True
                break
        if not crafted:
            self.spawn_item("energy_dust", block.center_x, block.center_y + SPRITE_PIXEL_SIZE)

    def eject_items(self, block):
        ejected = False
        t = block.block_type
        if t == "press":
            for _ in range(getattr(block, 'scrap_count', 0)): self.spawn_item("scrap", block.center_x,
                                                                              block.center_y + 64)
            for _ in range(getattr(block, 'dust_count', 0)): self.spawn_item("dust", block.center_x,
                                                                             block.center_y + 64)
            for _ in range(getattr(block, 'shard_count', 0)): self.spawn_item("shard", block.center_x,
                                                                              block.center_y + 64)
            block.scrap_count = block.dust_count = block.shard_count = 0
            ejected = True
        elif t == "furnace":
            for _ in range(getattr(block, 'ore_count', 0)): self.spawn_item(getattr(block, 'ore_type', "copper"),
                                                                            block.center_x, block.center_y + 64)
            for _ in range(getattr(block, 'energy_count', 0)): self.spawn_item("energy_dust", block.center_x,
                                                                               block.center_y + 64)
            block.ore_count = block.energy_count = 0
            ejected = True
        elif t == "assembler" and getattr(block, 'items_loaded', []):
            for i in block.items_loaded: self.spawn_item(i, block.center_x, block.center_y + 64)
            block.items_loaded.clear()
            ejected = True
        elif t == "chem_lab":
            for _ in range(getattr(block, 'spore_count', 0)): self.spawn_item("spore", block.center_x,
                                                                              block.center_y + 64)
            for _ in range(getattr(block, 'dust_count', 0)): self.spawn_item("energy_dust", block.center_x,
                                                                             block.center_y + 64)
            block.spore_count = block.dust_count = 0
            ejected = True
        elif t == "chest" and hasattr(block, 'inventory'):
            for item_type, count in block.inventory.items():
                for _ in range(count): self.spawn_item(item_type, block.center_x, block.center_y + 64)
            block.inventory.clear()
            ejected = True

    def get_hover_info(self, block):
        items = []
        t = getattr(block, 'block_type', '')
        if t == "chest":
            for k, v in getattr(block, 'inventory', {}).items():
                if v > 0: items.append((k, v))
        elif t == "furnace":
            ore_t = getattr(block, 'ore_type', 'copper')
            if getattr(block, 'ore_count', 0) > 0: items.append((ore_t, block.ore_count))
            if getattr(block, 'energy_count', 0) > 0: items.append(("energy_dust", block.energy_count))
        elif t == "press":
            if getattr(block, 'scrap_count', 0) > 0: items.append(("scrap", block.scrap_count))
            if getattr(block, 'dust_count', 0) > 0: items.append(("dust", block.dust_count))
            if getattr(block, 'shard_count', 0) > 0: items.append(("shard", block.shard_count))
        elif t == "assembler":
            from collections import Counter
            loaded = Counter(getattr(block, 'items_loaded', []))
            for k, v in loaded.items(): items.append((k, v))
        elif t == "chem_lab":
            if getattr(block, 'spore_count', 0) > 0: items.append(("spore", block.spore_count))
            if getattr(block, 'dust_count', 0) > 0: items.append(("energy_dust", block.dust_count))
        elif t == "terminal":
            if getattr(block, 'uranium_count', 0) > 0: items.append(("uranium_rod", block.uranium_count))
        return items

    def setup(self):
        arcade.set_background_color(arcade.color.BLACK)
        self.player_list.clear()
        self.items_list.clear()
        self.particle_list.clear()
        self.player_list.append(self.player)

        self.is_paused = False
        self.is_dead = False
        self.pause_manager.disable()
        self.load_inventory()

        self.world.update_chunks(self.player.center_x, self.player.center_y)
        solid_walls = [self.world.wall_list, self.world.fragile_list, self.world.metal_list, self.world.dust_list]
        self.physics_engine = arcade.PhysicsEnginePlatformer(self.player, gravity_constant=GRAVITY, walls=solid_walls)

    def on_draw(self):
        self.clear()
        self.camera.use()

        self.world.acid_list.draw()
        self.world.biomass_list.draw()
        self.world.uranium_list.draw()
        self.world.spikes_list.draw()
        self.world.geyser_list.draw()
        self.world.monolith_list.draw()

        self.world.interactables_list.draw()
        self.world.wall_list.draw()
        self.world.metal_list.draw()
        self.world.dust_list.draw()
        self.world.fragile_list.draw()
        self.world.bouncy_list.draw()
        self.world.hazard_list.draw()

        self.items_list.draw()
        self.particle_list.draw()

        if not self.is_dead:
            self.player_list.draw()

        # UI над игроком
        selected_item = self.slot_contents[self.selected_slot_index]
        if not self.is_dead and selected_item and self.player.inventory.get(selected_item, 0) > 0:
            tex = self.item_textures.get(selected_item, self.world.tex_item_dust)
            arcade.draw_texture_rect(tex, arcade.XYWH(self.player.center_x, self.player.top + 10, 32, 32))

        for t in self.damage_texts: t.draw()

        if self.player.center_y < LEVEL_2_START_Y * SPRITE_PIXEL_SIZE:
            arcade.draw_rect_filled(
                arcade.XYWH(self.camera.position.x, self.camera.position.y, VIRTUAL_WIDTH * 2, VIRTUAL_HEIGHT * 2),
                (0, 0, 0, 180))

        if self.hovered_block and not self.is_dead:
            info = self.get_hover_info(self.hovered_block)
            if info:
                box_width = 80
                box_height = len(info) * 26 + 10
                start_y = self.hovered_block.top + 10 + box_height / 2
                arcade.draw_rect_filled(arcade.XYWH(self.hovered_block.center_x, start_y, box_width, box_height),
                                        (0, 0, 0, 200))
                arcade.draw_rect_outline(arcade.XYWH(self.hovered_block.center_x, start_y, box_width, box_height),
                                         arcade.color.GRAY, 2)

                for i, (item_name, count) in enumerate(info):
                    tex = self.item_textures.get(item_name, self.world.tex_item_dust)
                    y_pos = self.hovered_block.top + 20 + i * 26
                    arcade.draw_texture_rect(tex, arcade.XYWH(self.hovered_block.center_x - 15, y_pos, 24, 24))
                    arcade.draw_text(f"x{count}", self.hovered_block.center_x + 5, y_pos, arcade.color.WHITE, 14,
                                     anchor_y="center", bold=True)

        if not self.is_dead:
            self.ui.draw(self.player, self.selected_slot_index, self.slot_contents, self.show_interact_hint,
                         self.show_teleport_menu)

        self.gui_camera.use()
        arcade.draw_text(f"Глубина: {self.max_depth}м", 20, 20, arcade.color.WHITE, 18, bold=True)

        if self.is_dead:
            w = arcade.get_window()
            arcade.draw_rect_filled(arcade.XYWH(w.width / 2, w.height / 2, w.width, w.height), (20, 0, 0, 220))
            arcade.draw_text("ВЫ ПОГИБЛИ", w.width / 2, w.height / 2 + 50, arcade.color.RED, 54, anchor_x="center",
                             bold=True)
            arcade.draw_text(f"Достигнутая глубина: {self.max_depth}м", w.width / 2, w.height / 2 - 10,
                             arcade.color.WHITE, 24, anchor_x="center")
            arcade.draw_text("Нажмите ПРОБЕЛ, чтобы возродиться", w.width / 2, w.height / 2 - 60,
                             arcade.color.LIGHT_GRAY, 16, anchor_x="center")

        elif self.is_paused:
            w = arcade.get_window()
            arcade.draw_rect_filled(arcade.XYWH(w.width / 2, w.height / 2, w.width, w.height), (0, 0, 0, 220))
            self.pause_manager.draw()

    def on_update(self, delta_time):
        if self.is_paused or self.is_dead: return
        self.time_elapsed += delta_time

        # Считаем глубину (-y)
        current_depth = max(0, int(-self.player.center_y / SPRITE_PIXEL_SIZE))
        if current_depth > self.max_depth:
            self.max_depth = current_depth

        if not self.show_teleport_menu:
            self.player.update_movement()
            self.physics_engine.update()
            self.player.update(delta_time)
            self.particle_list.update(delta_time)

            for t in self.damage_texts[:]:
                t.update()
                if t.alpha <= 0: self.damage_texts.remove(t)

            self.world.update_chunks(self.player.center_x, self.player.center_y)
            self.update_items(delta_time)
            self.update_interactions(delta_time)
            self.update_world_blocks(delta_time)

        self.center_camera_to_player()

    def update_world_blocks(self, dt):
        for geyser in self.world.geyser_list:
            geyser.timer += dt
            if geyser.timer > 3.0:
                geyser.timer = 0
                if abs(self.player.center_x - geyser.center_x) < 40 and self.player.bottom >= geyser.top and self.player.bottom < geyser.top + 100:
                    self.player.change_y = 20
                    for _ in range(5): self.particle_list.append(
                        WalkingParticle(geyser.center_x, geyser.top, (200, 255, 255, 100)))

        for metal in self.world.metal_list:
            if metal.block_type_id in (BLOCK_METAL,
                                       BLOCK_METAL2) and metal.center_y < LEVEL_2_START_Y * SPRITE_PIXEL_SIZE:
                if arcade.check_for_collision_with_list(metal, self.world.acid_list):
                    metal.dissolve_timer += dt
                    if metal.dissolve_timer > 5.0:
                        self.world.remove_block(metal)
                        for _ in range(3): self.particle_list.append(
                            WalkingParticle(metal.center_x, metal.center_y, COLOR_ACID))

    def update_items(self, delta_time):
        solid_walls = [self.world.wall_list, self.world.metal_list, self.world.fragile_list, self.world.dust_list]

        for item in self.items_list:
            item.timer += delta_time
            item.center_x += item.change_x
            item.center_y += item.change_y
            item.change_y -= GRAVITY * 0.5
            item.change_x *= 0.95

            if item.item_type == "acid_flask" and item.is_thrown:
                if arcade.check_for_collision_with_list(item, self.world.wall_list):
                    item.remove_from_sprite_lists()
                    wx, wy = int(item.center_x // SPRITE_PIXEL_SIZE), int(item.center_y // SPRITE_PIXEL_SIZE)
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            for b in arcade.get_sprites_at_point(((wx + dx) * 64 + 32, (wy + dy) * 64 + 32),
                                                                 self.world.wall_list):
                                if b.texture not in (self.world.tex_core,
                                                     self.world.tex_monolith): self.world.remove_block(b)
                    for _ in range(15): self.particle_list.append(
                        WalkingParticle(item.center_x, item.center_y, COLOR_ACID))
                    continue

            if any(arcade.check_for_collision_with_list(item, w) for w in solid_walls):
                item.change_y = item.change_x = 0

            item_consumed = False
            if item.is_thrown:
                for block in arcade.check_for_collision_with_list(item, self.world.interactables_list):
                    t = getattr(block, 'block_type', '')
                    if not hasattr(block,
                                   'scrap_count'): block.scrap_count = block.ore_count = block.energy_count = block.dust_count = block.shard_count = block.spore_count = block.uranium_count = 0
                    if not hasattr(block, 'items_loaded'): block.items_loaded = []

                    if t == "extractor" and item.item_type == "dust":
                        item.remove_from_sprite_lists()
                        self.player.mana = min(self.player.max_mana, self.player.mana + MANA_REGEN_FROM_ITEM)
                        item_consumed = True

                    elif t == "chest":
                        if not hasattr(block, 'inventory'): block.inventory = {}
                        if len(block.inventory) < 10 or item.item_type in block.inventory:
                            block.inventory[item.item_type] = block.inventory.get(item.item_type, 0) + 1
                            item.remove_from_sprite_lists()
                            item_consumed = True

                    elif t == "press":
                        if item.item_type == "scrap":
                            block.scrap_count += 1; item_consumed = True
                        elif item.item_type == "dust":
                            block.dust_count += 1; item_consumed = True
                        elif item.item_type == "shard":
                            block.shard_count += 1; item_consumed = True
                        elif item.item_type == "uranium_ore":
                            item.remove_from_sprite_lists()
                            self.spawn_item("uranium_rod", block.center_x, block.center_y + 64)
                            item_consumed = True
                        if item_consumed: item.remove_from_sprite_lists()

                        if block.scrap_count >= 2: block.scrap_count -= 2; self.spawn_item("metal2_block",
                                                                                           block.center_x,
                                                                                           block.center_y + 64)
                        while block.dust_count > 0 and block.shard_count > 0:
                            block.dust_count -= 1
                            block.shard_count -= 1
                            self.spawn_item("energy_dust", block.center_x, block.center_y + 64)

                    elif t == "furnace":
                        if item.item_type in ("copper", "titanium_ore"):
                            block.ore_count += 1
                            block.ore_type = item.item_type
                            item_consumed = True
                        elif item.item_type == "energy_dust":
                            block.energy_count += 1; item_consumed = True
                        if item_consumed: item.remove_from_sprite_lists()

                        while block.ore_count > 0 and block.energy_count > 0:
                            block.ore_count -= 1
                            block.energy_count -= 1
                            res = "titanium_ingot" if getattr(block, 'ore_type',
                                                              "copper") == "titanium_ore" else "copper_ingot"
                            self.spawn_item(res, block.center_x, block.center_y + 64)

                    elif t == "chem_lab":
                        if item.item_type == "spore":
                            block.spore_count += 1; item_consumed = True
                        elif item.item_type == "energy_dust":
                            block.dust_count += 1; item_consumed = True
                        if item_consumed: item.remove_from_sprite_lists()
                        while block.spore_count > 0 and block.dust_count > 0:
                            block.spore_count -= 1
                            block.dust_count -= 1
                            self.spawn_item("acid_flask", block.center_x, block.center_y + 64)

                    elif t == "terminal" and item.item_type == "uranium_rod":
                        block.uranium_count += 1
                        item.remove_from_sprite_lists()
                        item_consumed = True
                        if block.uranium_count >= 5:
                            block.uranium_count = 0
                            self.spawn_item("quantum_drill", block.center_x, block.center_y + 64)

                    elif t == "assembler":
                        if item.item_type == "energy_dust":
                            self.process_assembler_craft(block); item_consumed = True
                        else:
                            block.items_loaded.append(item.item_type); item_consumed = True
                        if item_consumed: item.remove_from_sprite_lists()

                    if item_consumed: break

            if not item_consumed and item.timer > 0.5:
                dist = math.hypot(self.player.center_x - item.center_x, self.player.center_y - item.center_y)
                if (not item.is_thrown or (abs(item.change_x) < 0.5 and abs(item.change_y) < 0.5)) and dist < 150:
                    ang = math.atan2(self.player.center_y - item.center_y, self.player.center_x - item.center_x)
                    item.change_x += math.cos(ang) * 1.5
                    item.change_y += math.sin(ang) * 1.5
                if dist < 40:
                    item.remove_from_sprite_lists()
                    self.add_to_inventory(item.item_type)

    def update_interactions(self, dt):
        if arcade.check_for_collision_with_list(self.player, self.world.hazard_list):
            if not self.is_dead:
                self.is_dead = True
                self.player.hp = 0

        for block in arcade.check_for_collision_with_list(self.player, self.world.bouncy_list):
            dx, dy = self.player.center_x - block.center_x, self.player.center_y - block.center_y
            dist = max(0.1, math.hypot(dx, dy))
            mult = 3.0 if getattr(block, 'block_type', '') == "reflector" and self.player.dash_timer > 0 else 1.0
            self.player.change_x += (dx / dist) * IMPULSE_STRENGTH * 0.8 * mult
            self.player.change_y += (dy / dist) * IMPULSE_STRENGTH * 0.8 * mult

        if arcade.check_for_collision_with_list(self.player, self.world.acid_list):
            self.player.mana -= 100 * dt
            if self.time_elapsed % 1.0 < 0.1: self.take_damage(5)

        self.player.on_biomass = len(arcade.check_for_collision_with_list(self.player, self.world.biomass_list)) > 0

        if arcade.check_for_collision_with_list(self.player, self.world.spikes_list):
            if self.time_elapsed % 1.0 < 0.1: self.take_damage(15)

        if arcade.check_for_collision_with_list(self.player, self.world.uranium_list):
            self.uranium_timer += dt
            if self.uranium_timer > 2.0 and self.time_elapsed % 1.0 < 0.1:
                self.take_damage(10)
                self.player.mana -= 50
        else:
            self.uranium_timer = 0

        near_battery = len(arcade.get_sprites_in_rect(arcade.XYWH(self.player.center_x, self.player.center_y, 400, 400),
                                                      self.world.battery_list)) > 0
        self.player.max_mana = MAX_MANA + 200 if near_battery else MAX_MANA
        if self.player.mana > self.player.max_mana: self.player.mana = self.player.max_mana

        self.show_interact_hint = False
        self.current_interactable = None
        for block in self.world.interactables_list:
            if math.hypot(self.player.center_x - block.center_x, self.player.center_y - block.center_y) < 80:
                self.show_interact_hint = True
                self.current_interactable = block
                break

    def center_camera_to_player(self):
        self.camera.position = (
            self.camera.position.x + (self.player.center_x - self.camera.position.x) * 0.1,
            self.camera.position.y + (self.player.center_y - self.camera.position.y) * 0.1
        )

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.camera = arcade.camera.Camera2D()
        self.gui_camera = arcade.camera.Camera2D()
        self.ui.camera = arcade.camera.Camera2D()
        if hasattr(self.pause_manager, 'on_resize'):
            self.pause_manager.on_resize(width, height)

    def on_mouse_scroll(self, x, y, sx, sy):
        if self.is_paused or self.is_dead: return
        if sy > 0:
            self.selected_slot_index = (self.selected_slot_index - 1) % UI_HOTBAR_SLOTS
        elif sy < 0:
            self.selected_slot_index = (self.selected_slot_index + 1) % UI_HOTBAR_SLOTS

    def on_mouse_motion(self, x, y, dx, dy):
        if self.is_paused or self.show_teleport_menu or self.is_dead: return
        world_coords = self.camera.unproject((x, y))
        world_x, world_y = world_coords[0], world_coords[1]
        self.player.facing_right = world_x > self.player.center_x
        self.player.texture = self.player.tex_right if self.player.facing_right else self.player.tex_left

        sprites = arcade.get_sprites_at_point((world_x, world_y), self.world.interactables_list)
        self.hovered_block = sprites[0] if sprites else None

    def on_key_press(self, key, modifiers):
        if key == arcade.key.F11:
            self.window.set_fullscreen(not self.window.fullscreen)
            return

        if self.is_dead:
            if key == arcade.key.SPACE:
                self.player.respawn()
                self.player.left_pressed = False
                self.player.right_pressed = False
                self.is_dead = False
                self.save_game()
            return

        if key in (arcade.key.ESCAPE, arcade.key.TAB):
            if self.show_teleport_menu:
                self.show_teleport_menu = False
            else:
                self.toggle_pause()
            return

        if self.is_paused: return

        if self.show_teleport_menu:
            if key == arcade.key.KEY_1:
                self.player.center_x, self.player.center_y = self.player.start_x, self.player.start_y
                self.show_teleport_menu = False
            elif key == arcade.key.E:
                self.show_teleport_menu = False
            return

        if key == arcade.key.E and self.show_interact_hint and self.current_interactable:
            if getattr(self.current_interactable, 'block_type', '') == "teleporter":
                self.show_teleport_menu = True
            else:
                self.eject_items(self.current_interactable)

        if key in (arcade.key.W, arcade.key.UP, arcade.key.SPACE) and self.physics_engine.can_jump():
            self.player.change_y = PLAYER_JUMP_SPEED
        elif key in (arcade.key.A, arcade.key.LEFT):
            self.player.left_pressed = True
        elif key in (arcade.key.D, arcade.key.RIGHT):
            self.player.right_pressed = True

        elif arcade.key.KEY_1 <= key <= arcade.key.KEY_9:
            self.selected_slot_index = key - arcade.key.KEY_1
        elif key == arcade.key.KEY_0:
            self.selected_slot_index = 9

        elif key == arcade.key.Q:
            item = self.slot_contents[self.selected_slot_index]
            if item and self.remove_from_inventory(item, 1):
                self.spawn_item(item, self.player.center_x, self.player.center_y + 10, is_thrown=True,
                                direction=1 if self.player.facing_right else -1)

    def on_key_release(self, key, modifiers):
        if key in (arcade.key.A, arcade.key.LEFT):
            self.player.left_pressed = False
        elif key in (arcade.key.D, arcade.key.RIGHT):
            self.player.right_pressed = False

    def on_mouse_press(self, x, y, button, modifiers):
        if self.is_paused or self.show_teleport_menu or self.is_dead: return
        world_coords = self.camera.unproject((x, y))
        world_x, world_y = world_coords[0], world_coords[1]

        if button == arcade.MOUSE_BUTTON_LEFT:
            if self.player.mana >= DASH_MANA_COST and not self.player.on_biomass:
                self.player.mana -= DASH_MANA_COST
                self.player.apply_impulse(world_x, world_y)

        elif button == arcade.MOUSE_BUTTON_RIGHT:
            if math.hypot(self.player.center_x - world_x, self.player.center_y - world_y) > 300: return

            selected = self.slot_contents[self.selected_slot_index]

            if selected == "acid_flask" and self.player.inventory.get("acid_flask", 0) > 0:
                self.player.mana = min(self.player.max_mana, self.player.mana + 100)
                self.remove_from_inventory("acid_flask", 1)
                return

            machine_blocks = ["metal2_block", "furnace", "assembler", "teleporter", "extractor", "press",
                              "titanium_block", "glass_block", "chem_lab", "battery", "reflector", "chest"]

            wx, wy = int(world_x // SPRITE_PIXEL_SIZE), int(world_y // SPRITE_PIXEL_SIZE)
            hit_lists = [
                self.world.wall_list, self.world.fragile_list, self.world.metal_list,
                self.world.dust_list, self.world.interactables_list,
                self.world.biomass_list, self.world.spikes_list
            ]

            if selected in machine_blocks and self.player.inventory.get(selected, 0) > 0:
                can_place = True
                for lst in hit_lists:
                    if arcade.get_sprites_at_point((world_x, world_y), lst):
                        can_place = False
                        break

                if can_place:
                    b = BLOCK_METAL2
                    if selected == "furnace":
                        b = BLOCK_FURNACE
                    elif selected == "assembler":
                        b = BLOCK_ASSEMBLER
                    elif selected == "teleporter":
                        b = BLOCK_TELEPORTER
                    elif selected == "extractor":
                        b = BLOCK_EXTRACTOR
                    elif selected == "press":
                        b = BLOCK_PRESS
                    elif selected == "chest":
                        b = BLOCK_CHEST
                    elif selected == "titanium_block":
                        b = BLOCK_TITANIUM
                    elif selected == "glass_block":
                        b = BLOCK_GLASS
                    elif selected == "chem_lab":
                        b = BLOCK_CHEM_LAB
                    elif selected == "battery":
                        b = BLOCK_BATTERY
                    elif selected == "reflector":
                        b = BLOCK_REFLECTOR

                    self.world.add_block(wx, wy, b)
                    self.remove_from_inventory(selected, 1)
                return

            blocks_to_break = []
            for lst in hit_lists:
                blocks_to_break.extend(arcade.get_sprites_at_point((world_x, world_y), lst))

            if not blocks_to_break: return
            target_block = blocks_to_break[0]

            blocks_to_process = [target_block]
            if selected == "quantum_drill" and target_block.texture not in (self.world.tex_core,
                                                                            self.world.tex_monolith):
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    for lst in hit_lists:
                        blocks_to_process.extend(
                            arcade.get_sprites_at_point(((wx + dx) * 64 + 32, (wy + dy) * 64 + 32), lst))

            for block in set(blocks_to_process):
                if block.texture in (self.world.tex_core, self.world.tex_monolith):
                    if selected in ("pickaxe", "quantum_drill"):
                        if block.texture == self.world.tex_monolith: continue
                        self.world.remove_block(block)
                        for _ in range(5): self.particle_list.append(
                            WalkingParticle(block.center_x, block.center_y, (80, 20, 20, 100)))
                    continue

                if block in self.world.interactables_list:
                    if selected in ("pickaxe", "quantum_drill"):
                        self.eject_items(block)
                        self.world.remove_block(block)
                        t = getattr(block, 'block_type', '')
                        if t in ("teleporter", "furnace", "assembler", "extractor", "press", "chem_lab", "battery",
                                 "reflector", "chest"):
                            self.spawn_item(t, block.center_x, block.center_y)
                    continue

                hard_blocks = [
                    self.world.tex_deep_slate,
                    self.world.tex_titanium_ore,
                    self.world.tex_uranium_ore,
                    self.world.tex_titanium,
                    self.world.tex_glass
                ]

                if block.texture in hard_blocks and selected not in ("pickaxe", "quantum_drill"):
                    continue

                tex = block.texture
                if tex == self.world.tex_copper_ore:
                    if random.random() < COPPER_DROP_CHANCE: self.spawn_item("copper", block.center_x, block.center_y)
                elif tex == self.world.tex_titanium_ore:
                    self.spawn_item("titanium_ore", block.center_x, block.center_y)
                elif tex == self.world.tex_uranium_ore:
                    self.spawn_item("uranium_ore", block.center_x, block.center_y)
                elif tex == self.world.tex_shroom:
                    self.spawn_item("spore", block.center_x, block.center_y)
                elif block in self.world.metal_list:
                    if random.random() < 0.8: self.spawn_item("scrap", block.center_x, block.center_y)
                elif block in self.world.fragile_list:
                    if random.random() < SHARD_DROP_CHANCE: self.spawn_item("shard", block.center_x, block.center_y)
                elif block in self.world.wall_list and random.random() < 0.3:
                    self.spawn_item("dust", block.center_x, block.center_y)

                self.world.remove_block(block)
                for _ in range(5): self.particle_list.append(
                    WalkingParticle(block.center_x, block.center_y, (100, 100, 100, 100)))