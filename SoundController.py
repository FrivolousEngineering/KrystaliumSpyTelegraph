import contextlib
import random
import os
with contextlib.redirect_stdout(None):
    import pygame


class SoundController:
    sound_completed_event = pygame.USEREVENT + 1

    def __init__(self):
        """
        Simple wrapper around chanel setup and handling playing of sounds.
        """
        # Setup all the sound stuff
        pygame.mixer.init()

        self._clicks_short = self._loadSounds("Sounds/ShortClicks")
        self._clicks_long = self._loadSounds("Sounds/LongClicks")

        self._final_bell = pygame.mixer.Sound("Sounds/final_bell.mp3")
        self._bell_double = pygame.mixer.Sound("Sounds/final_bell_double.mp3")

        self._click_sound_channel = pygame.mixer.Channel(0)
        self._click_sound_channel.set_endevent(self.sound_completed_event)

        # As we don't want a complete event for the bell, we use a separate channel
        self._bell_sound_channel = pygame.mixer.Channel(1)

    def _loadSounds(self, folder_path):
        sounds = []
        # List all files in the folder and filter for .mp3 files
        for filename in os.listdir(folder_path):
            if filename.endswith(".mp3"):
                full_path = os.path.join(folder_path, filename)
                sounds.append(pygame.mixer.Sound(full_path))
        return sounds

    def playLongClick(self):
        self._click_sound_channel.queue(random.choice(self._clicks_long))

    def playShortClick(self):
        self._click_sound_channel.queue(random.choice(self._clicks_short))

    def playBell(self):
        self._bell_sound_channel.queue(self._final_bell)

    def playBellDouble(self):
        self._bell_sound_channel.queue(self._bell_double)