import arcade
import os
import random


class MusicManager:
    """Глобальный менеджер музыки для плавного переключения случайных треков"""

    def __init__(self, music_dir="assets/music"):
        self.music_dir = music_dir
        self.music_list = []
        self.current_sound = None
        self.current_player = None

        self.max_volume = 0.3
        self.fade_time = 3.0

        self.state = "stopped"
        self.time_playing = 0.0
        self.current_duration = 0.0
        self.last_song = None

        os.makedirs(music_dir, exist_ok=True)
        self.load_playlist()

    def load_playlist(self):
        self.music_list = []
        if os.path.exists(self.music_dir):
            for f in os.listdir(self.music_dir):
                if f.lower().endswith(('.mp3', '.wav', '.ogg')):
                    self.music_list.append(os.path.join(self.music_dir, f))

    def play_next(self):
        if not self.music_list:
            return

        next_song = random.choice(self.music_list)
        if len(self.music_list) > 1 and next_song == self.last_song:
            next_song = random.choice([s for s in self.music_list if s != self.last_song])

        self.last_song = next_song
        self.current_sound = arcade.Sound(next_song)

        self.current_player = self.current_sound.play(volume=0.0)
        self.state = "fade_in"
        self.time_playing = 0.0

        try:
            self.current_duration = self.current_sound.get_length()
        except Exception:
            self.current_duration = 30.0

    def update(self, dt):
        if not self.music_list:
            return

        if self.current_player is None or not self.current_player.playing:
            if self.state != "stopped":
                self.play_next()
            return

        self.time_playing += dt

        if self.state == "playing" and (self.current_duration - self.time_playing) <= self.fade_time:
            self.state = "fade_out"

        if self.state == "fade_in":
            new_volume = self.current_player.volume + (self.max_volume / self.fade_time) * dt
            if new_volume >= self.max_volume:
                self.current_player.volume = self.max_volume
                self.state = "playing"
            else:
                self.current_player.volume = new_volume

        elif self.state == "fade_out":
            new_volume = self.current_player.volume - (self.max_volume / self.fade_time) * dt
            if new_volume <= 0.0:
                self.current_player.volume = 0.0
                self.current_player.pause()
                self.state = "stopped"
                self.play_next()
            else:
                self.current_player.volume = new_volume