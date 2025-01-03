
import contextlib

with contextlib.redirect_stdout(None):
    import pygame


class SoundController:
    sound_completed_event = pygame.USEREVENT + 1

    def __init__(self):
        # Setup all the sound stuff
        pygame.mixer.init()
        self._click_short = pygame.mixer.Sound("click_short.mp3")
        self._click_long = pygame.mixer.Sound("click_long.mp3")
        self._final_bell = pygame.mixer.Sound("final_bell.mp3")

        self._click_sound_channel = pygame.mixer.Channel(0)
        self._click_sound_channel.set_endevent(self.sound_completed_event)

        # As we don't want a complete event for the bell, we use a separate channel
        self._bell_sound_channel = pygame.mixer.Channel(1)

    def playLongClick(self):
        self._click_sound_channel.queue(self._click_long)

    def playShortClick(self):
        self._click_sound_channel.queue(self._click_short)

    def playBell(self):
        self._bell_sound_channel.queue(self._final_bell)