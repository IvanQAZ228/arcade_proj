import arcade
import random
import os
import json
import math
from .constants import *


def get_texture(filepath, fallback_color, size=SPRITE_PIXEL_SIZE):
    if os.path.exists(filepath):
        return arcade.load_texture(filepath)
    return arcade.make_soft_square_texture(size, fallback_color, outer_alpha=255)


class Chunk:
    def __init__(self, cx, cy, world):
        self.cx = cx
        self.cy = cy
        self.world = world
        self.blocks_data = {}
        self.sprites = []
        self.save_path = f"saves/chunk_{cx}_{cy}.json"

    def generate_or_load(self):
        if os.path.exists(self.save_path):
            with open(self.save_path, "r") as f:
                raw_data = json.load(f)

            for key, val in raw_data.items():
                if isinstance(val, dict):
                    self.blocks_data[key] = val
                else:
                    self.blocks_data[key] = {"type": val, "meta": {}}
        else:
            for lx in range(CHUNK_SIZE):
                for ly in range(CHUNK_SIZE):
                    wx = self.cx * CHUNK_SIZE + lx
                    wy = self.cy * CHUNK_SIZE + ly
                    block_type = self.world.get_default_block(wx, wy)
                    self.blocks_data[f"{lx}_{ly}"] = {"type": block_type, "meta": {}}

        for key, data in self.blocks_data.items():
            block_type = data.get("type", BLOCK_EMPTY)
            meta = data.get("meta", {})
            if block_type == BLOCK_EMPTY: continue

            lx, ly = map(int, key.split('_'))
            wx = self.cx * CHUNK_SIZE + lx
            wy = self.cy * CHUNK_SIZE + ly
            self.world._create_sprite_for_block(self, wx, wy, lx, ly, block_type, meta)

    def save(self):
        for sprite in self.sprites:
            key = f"{sprite.lx}_{sprite.ly}"
            if not hasattr(sprite, 'block_type'): continue

            meta = {}
            t = sprite.block_type
            if t == "chest":
                meta["inv"] = getattr(sprite, 'inventory', {})
            elif t == "furnace":
                meta["ore"] = getattr(sprite, 'ore_count', 0)
                meta["en"] = getattr(sprite, 'energy_count', 0)
                meta["ore_t"] = getattr(sprite, 'ore_type', "copper")
            elif t == "press":
                meta["sc"] = getattr(sprite, 'scrap_count', 0)
                meta["du"] = getattr(sprite, 'dust_count', 0)
                meta["sh"] = getattr(sprite, 'shard_count', 0)
            elif t == "assembler":
                meta["ld"] = getattr(sprite, 'items_loaded', [])
            elif t == "chem_lab":
                meta["sp"] = getattr(sprite, 'spore_count', 0)
                meta["du"] = getattr(sprite, 'dust_count', 0)
            elif t == "terminal":
                meta["ur"] = getattr(sprite, 'uranium_count', 0)

            if key in self.blocks_data:
                self.blocks_data[key]["meta"] = meta

        with open(self.save_path, "w") as f:
            json.dump(self.blocks_data, f)

    def unload(self):
        self.save()
        for sprite in self.sprites:
            sprite.remove_from_sprite_lists()


class World:
    def __init__(self):
        self.wall_list = arcade.SpriteList(use_spatial_hash=True)
        self.fragile_list = arcade.SpriteList(use_spatial_hash=True)
        self.bouncy_list = arcade.SpriteList(use_spatial_hash=True)
        self.hazard_list = arcade.SpriteList(use_spatial_hash=True)
        self.metal_list = arcade.SpriteList(use_spatial_hash=True)
        self.dust_list = arcade.SpriteList(use_spatial_hash=True)
        self.interactables_list = arcade.SpriteList(use_spatial_hash=True)

        self.acid_list = arcade.SpriteList(use_spatial_hash=True)
        self.biomass_list = arcade.SpriteList(use_spatial_hash=True)
        self.uranium_list = arcade.SpriteList(use_spatial_hash=True)
        self.geyser_list = arcade.SpriteList()
        self.spikes_list = arcade.SpriteList(use_spatial_hash=True)
        self.monolith_list = arcade.SpriteList(use_spatial_hash=True)
        self.battery_list = arcade.SpriteList()

        self.active_chunks = {}
        os.makedirs("saves", exist_ok=True)

        self.tex_quantum = get_texture("assets/textures/block_quantum.png", COLOR_QUANTUM)
        self.tex_core = get_texture("assets/textures/block_core.png", COLOR_CORE)
        self.tex_fragile = get_texture("assets/textures/block_fragile.png", COLOR_FRAGILE)
        self.tex_bouncy = get_texture("assets/textures/block_bouncy.png", COLOR_BOUNCY)
        self.tex_hazard = get_texture("assets/textures/block_hazard.png", COLOR_HAZARD)
        self.tex_metal = get_texture("assets/textures/block_metal.png", COLOR_METAL)
        self.tex_metal2 = get_texture("assets/textures/block_metal2.png", COLOR_METAL2)
        self.tex_dust = get_texture("assets/textures/block_dust.png", COLOR_DUST)

        self.tex_extractor = get_texture("assets/textures/block_extractor.png", COLOR_EXTRACTOR)
        self.tex_teleporter = get_texture("assets/textures/block_teleporter.png", COLOR_TELEPORTER)
        self.tex_press = get_texture("assets/textures/block_press.png", COLOR_PRESS)
        self.tex_assembler = get_texture("assets/textures/block_assembler.png", COLOR_ASSEMBLER)
        self.tex_furnace = get_texture("assets/textures/block_furnace.png", COLOR_FURNACE)
        self.tex_chest = get_texture("assets/textures/block_chest.png", COLOR_CHEST)  # Текстура сундука
        self.tex_copper_ore = get_texture("assets/textures/block_copper.png", COLOR_COPPER_ORE)

        self.tex_deep_slate = get_texture("assets/textures/block_deep_slate.png", COLOR_DEEP_SLATE)
        self.tex_titanium_ore = get_texture("assets/textures/block_titanium_ore.png", COLOR_TITANIUM_ORE)
        self.tex_uranium_ore = get_texture("assets/textures/block_uranium_ore.png", COLOR_URANIUM_ORE)
        self.tex_acid = get_texture("assets/textures/block_acid.png", COLOR_ACID)
        self.tex_shroom = get_texture("assets/textures/block_shroom.png", COLOR_SHROOM)
        self.tex_biomass = get_texture("assets/textures/block_biomass.png", COLOR_BIOMASS)
        self.tex_spikes = get_texture("assets/textures/block_spikes.png", COLOR_SPIKES)
        self.tex_geyser = get_texture("assets/textures/block_geyser.png", COLOR_GEYSER)
        self.tex_titanium = get_texture("assets/textures/block_titanium.png", COLOR_TITANIUM)
        self.tex_glass = get_texture("assets/textures/block_glass.png", COLOR_GLASS)
        self.tex_monolith = get_texture("assets/textures/block_monolith.png", COLOR_MONOLITH)
        self.tex_terminal = get_texture("assets/textures/block_terminal.png", COLOR_TERMINAL)
        self.tex_chem_lab = get_texture("assets/textures/block_chem_lab.png", COLOR_CHEM_LAB)
        self.tex_battery = get_texture("assets/textures/block_battery.png", COLOR_BATTERY)
        self.tex_reflector = get_texture("assets/textures/block_reflector.png", COLOR_REFLECTOR)

        self.tex_item_dust = get_texture("assets/textures/item_dust.png", COLOR_DUST_ITEM, size=24)
        self.tex_item_energy_dust = get_texture("assets/textures/item_energy_dust.png", COLOR_ENERGY_DUST_ITEM, size=24)
        self.tex_item_shard = get_texture("assets/textures/item_shard.png", COLOR_SHARD_ITEM, size=24)
        self.tex_item_scrap = get_texture("assets/textures/item_scrap.png", COLOR_SCRAP_ITEM, size=24)
        self.tex_item_copper_ingot = get_texture("assets/textures/item_copper_ingot.png", COLOR_COPPER_INGOT, size=24)
        self.tex_item_titanium_ingot = get_texture("assets/textures/item_titanium_ingot.png", COLOR_TITANIUM_INGOT,
                                                   size=24)
        self.tex_item_uranium_rod = get_texture("assets/textures/item_uranium_rod.png", COLOR_URANIUM_ROD, size=24)
        self.tex_item_spore = get_texture("assets/textures/item_spore.png", COLOR_SPORE, size=24)
        self.tex_item_acid_flask = get_texture("assets/textures/item_acid_flask.png", COLOR_ACID_FLASK, size=24)
        self.tex_item_quantum_drill = get_texture("assets/textures/item_quantum_drill.png", COLOR_DRILL, size=48)

    def get_default_block(self, wx, wy):
        if -7 <= wx <= 7 and 1 <= wy <= 9:
            if 1 <= wy <= 2 and -5 <= wx <= 5: return BLOCK_CORE
            if wx == 0 and wy == 3: return BLOCK_EXTRACTOR
            if wx == -2 and wy == 3: return BLOCK_TELEPORTER
            if wx == 2 and wy == 3: return BLOCK_PRESS
            if wx == 4 and wy == 3: return BLOCK_ASSEMBLER
            return BLOCK_EMPTY

        if LEVEL_2_START_Y <= wy <= LEVEL_2_START_Y + 2: return BLOCK_CORE

        random.seed(f"seed_{wx}_{wy}")
        noise = math.sin(wx * 0.2) * math.cos(wy * 0.2) + math.sin(wx * 0.05 + wy * 0.05)

        if wy < LEVEL_2_START_Y:
            if noise > 0.4: return BLOCK_EMPTY
            rand = random.random()
            if noise > 0.35 and rand < 0.5: return BLOCK_ACID
            if rand < 0.02:
                return BLOCK_MONOLITH
            elif rand < 0.04:
                return BLOCK_URANIUM_ORE
            elif rand < 0.06:
                return BLOCK_SHROOM
            elif rand < 0.10:
                return BLOCK_BIOMASS
            elif rand < 0.14:
                return BLOCK_GEYSER
            elif rand < 0.18:
                return BLOCK_SPIKES
            elif rand < 0.25:
                return BLOCK_TITANIUM_ORE
            return BLOCK_DEEP_SLATE

        if wy > 5: return BLOCK_EMPTY
        if wy == 5: return BLOCK_DUST
        if noise > 0.4: return BLOCK_EMPTY

        rand = random.random()
        if rand < 0.05:
            return BLOCK_FRAGILE
        elif rand < 0.08:
            return BLOCK_BOUNCY
        elif rand < 0.12:
            return BLOCK_HAZARD
        elif rand < 0.17:
            return BLOCK_COPPER_ORE
        elif rand < 0.25:
            return BLOCK_METAL
        elif rand < 0.40:
            return BLOCK_DUST
        return BLOCK_QUANTUM

    def _create_sprite_for_block(self, chunk, wx, wy, lx, ly, block_type, meta=None):
        if meta is None: meta = {}
        sprite = arcade.Sprite()
        sprite.block_type_id = block_type
        sprite.dissolve_timer = 0.0

        if block_type == BLOCK_CORE:
            sprite.texture = self.tex_core
        elif block_type == BLOCK_QUANTUM:
            sprite.texture = self.tex_quantum
        elif block_type == BLOCK_FRAGILE:
            sprite.texture = self.tex_fragile
        elif block_type == BLOCK_BOUNCY:
            sprite.texture = self.tex_bouncy
        elif block_type == BLOCK_HAZARD:
            sprite.texture = self.tex_hazard
        elif block_type == BLOCK_METAL:
            sprite.texture = self.tex_metal
        elif block_type == BLOCK_METAL2:
            sprite.texture = self.tex_metal2
        elif block_type == BLOCK_COPPER_ORE:
            sprite.texture = self.tex_copper_ore
        elif block_type == BLOCK_DUST:
            sprite.texture = self.tex_dust

        elif block_type == BLOCK_DEEP_SLATE:
            sprite.texture = self.tex_deep_slate
        elif block_type == BLOCK_TITANIUM_ORE:
            sprite.texture = self.tex_titanium_ore
        elif block_type == BLOCK_URANIUM_ORE:
            sprite.texture = self.tex_uranium_ore
        elif block_type == BLOCK_ACID:
            sprite.texture = self.tex_acid
        elif block_type == BLOCK_SHROOM:
            sprite.texture = self.tex_shroom
        elif block_type == BLOCK_BIOMASS:
            sprite.texture = self.tex_biomass
        elif block_type == BLOCK_SPIKES:
            sprite.texture = self.tex_spikes
        elif block_type == BLOCK_GEYSER:
            sprite.texture = self.tex_geyser
            sprite.timer = random.uniform(0, 3.0)
        elif block_type == BLOCK_TITANIUM:
            sprite.texture = self.tex_titanium
        elif block_type == BLOCK_GLASS:
            sprite.texture = self.tex_glass
        elif block_type == BLOCK_MONOLITH:
            sprite.texture = self.tex_monolith

        elif block_type == BLOCK_EXTRACTOR:
            sprite.texture = self.tex_extractor
            sprite.block_type = "extractor"
        elif block_type == BLOCK_TELEPORTER:
            sprite.texture = self.tex_teleporter
            sprite.block_type = "teleporter"
        elif block_type == BLOCK_PRESS:
            sprite.texture = self.tex_press
            sprite.block_type = "press"
            sprite.scrap_count = meta.get("sc", 0)
            sprite.dust_count = meta.get("du", 0)
            sprite.shard_count = meta.get("sh", 0)
        elif block_type == BLOCK_FURNACE:
            sprite.texture = self.tex_furnace
            sprite.block_type = "furnace"
            sprite.ore_count = meta.get("ore", 0)
            sprite.energy_count = meta.get("en", 0)
            sprite.ore_type = meta.get("ore_t", "copper")
        elif block_type == BLOCK_ASSEMBLER:
            sprite.texture = self.tex_assembler
            sprite.block_type = "assembler"
            sprite.items_loaded = meta.get("ld", [])
        elif block_type == BLOCK_CHEST:
            sprite.texture = self.tex_chest
            sprite.block_type = "chest"
            sprite.inventory = meta.get("inv", {})
        elif block_type == BLOCK_TERMINAL:
            sprite.texture = self.tex_terminal
            sprite.block_type = "terminal"
            sprite.uranium_count = meta.get("ur", 0)
        elif block_type == BLOCK_CHEM_LAB:
            sprite.texture = self.tex_chem_lab
            sprite.block_type = "chem_lab"
            sprite.spore_count = meta.get("sp", 0)
            sprite.dust_count = meta.get("du", 0)
        elif block_type == BLOCK_BATTERY:
            sprite.texture = self.tex_battery
            sprite.block_type = "battery"
        elif block_type == BLOCK_REFLECTOR:
            sprite.texture = self.tex_reflector
            sprite.block_type = "reflector"

        sprite.center_x = wx * SPRITE_PIXEL_SIZE + SPRITE_PIXEL_SIZE / 2
        sprite.center_y = wy * SPRITE_PIXEL_SIZE + SPRITE_PIXEL_SIZE / 2
        sprite.chunk = chunk
        sprite.lx = lx
        sprite.ly = ly

        chunk.sprites.append(sprite)

        if block_type in (BLOCK_CORE, BLOCK_QUANTUM, BLOCK_DEEP_SLATE, BLOCK_TITANIUM, BLOCK_GLASS):
            self.wall_list.append(sprite)
        elif block_type == BLOCK_FRAGILE:
            self.fragile_list.append(sprite)
        elif block_type in (BLOCK_BOUNCY, BLOCK_REFLECTOR):
            self.bouncy_list.append(sprite)
        elif block_type == BLOCK_HAZARD:
            self.hazard_list.append(sprite)
        elif block_type in (BLOCK_METAL, BLOCK_METAL2, BLOCK_COPPER_ORE, BLOCK_TITANIUM_ORE):
            self.metal_list.append(sprite)
        elif block_type == BLOCK_DUST:
            self.dust_list.append(sprite)
        elif block_type == BLOCK_ACID:
            self.acid_list.append(sprite)
        elif block_type == BLOCK_BIOMASS:
            self.biomass_list.append(sprite)
        elif block_type == BLOCK_URANIUM_ORE:
            self.uranium_list.append(sprite); self.wall_list.append(sprite)
        elif block_type == BLOCK_SPIKES:
            self.spikes_list.append(sprite)
        elif block_type == BLOCK_GEYSER:
            self.geyser_list.append(sprite); self.wall_list.append(sprite)
        elif block_type == BLOCK_MONOLITH:
            self.monolith_list.append(sprite); self.wall_list.append(sprite)
        elif block_type == BLOCK_BATTERY:
            self.battery_list.append(sprite); self.interactables_list.append(sprite); self.wall_list.append(sprite)
        elif block_type == BLOCK_SHROOM:
            self.fragile_list.append(sprite)

        elif block_type in (BLOCK_EXTRACTOR, BLOCK_TELEPORTER, BLOCK_PRESS, BLOCK_FURNACE, BLOCK_ASSEMBLER, BLOCK_CHEST,
                            BLOCK_TERMINAL, BLOCK_CHEM_LAB):
            self.interactables_list.append(sprite)

    def add_block(self, wx, wy, block_type):
        cx, cy = int(wx // CHUNK_SIZE), int(wy // CHUNK_SIZE)
        lx, ly = int(wx % CHUNK_SIZE), int(wy % CHUNK_SIZE)

        if (cx, cy) in self.active_chunks:
            chunk = self.active_chunks[(cx, cy)]
            chunk.blocks_data[f"{lx}_{ly}"] = {"type": block_type, "meta": {}}
            self._create_sprite_for_block(chunk, wx, wy, lx, ly, block_type, {})

    def update_chunks(self, player_x, player_y):
        chunk_x = int(player_x // (CHUNK_SIZE * SPRITE_PIXEL_SIZE))
        chunk_y = int(player_y // (CHUNK_SIZE * SPRITE_PIXEL_SIZE))

        needed_chunks = set()
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                needed_chunks.add((chunk_x + dx, chunk_y + dy))

        for (cx, cy) in list(self.active_chunks.keys()):
            if (cx, cy) not in needed_chunks:
                self.active_chunks[(cx, cy)].unload()
                del self.active_chunks[(cx, cy)]

        for (cx, cy) in needed_chunks:
            if (cx, cy) not in self.active_chunks:
                new_chunk = Chunk(cx, cy, self)
                new_chunk.generate_or_load()
                self.active_chunks[(cx, cy)] = new_chunk

    def remove_block(self, sprite):
        chunk = sprite.chunk
        chunk.blocks_data[f"{sprite.lx}_{sprite.ly}"] = {"type": BLOCK_EMPTY, "meta": {}}
        sprite.remove_from_sprite_lists()