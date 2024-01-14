import argparse
import logging
import queue
import sys
import random

from escpos import printer
import contextlib

with contextlib.redirect_stdout(None):
    import pygame

from Config import Config
from MorseImageCreator import MorseImageCreator

# Window size
WINDOW_WIDTH = 400
WINDOW_HEIGHT = 400
WINDOW_SURFACE = pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE

DARK_BLUE = (3, 5, 54)

# Pygame events
sound_completed_event = pygame.USEREVENT + 1
pause_between_tick_event = pygame.USEREVENT + 2
request_update_server_event = pygame.USEREVENT + 3

multi_line_config = Config("CENTER", 50, 20, 20, 10, 6, add_headers=True)
single_line_config = Config("LEFT", 75, 20, 20, 20, 1, add_headers=False)


class PygameWrapper:
    MIN_SPACE_PAUSE = 400
    MAX_SPACE_PAUSE = 500

    MIN_CHAR_PAUSE = 16
    MAX_CHAR_PAUSE = 64

    def __init__(self, fullscreen: bool = True):
        pygame.init()
        self._screen_width = 1280
        self._screen_height = 720
        if fullscreen:
            self._screen = pygame.display.set_mode((self._screen_width, self._screen_height), pygame.FULLSCREEN)
        else:
            self._screen = pygame.display.set_mode((self._screen_width, self._screen_height))
        self._clock = pygame.time.Clock()
        self._running = False

        self._click_short = pygame.mixer.Sound("click_short.mp3")
        self._click_long = pygame.mixer.Sound("click_long.mp3")

        self._channel1 = pygame.mixer.Channel(0)  # argument must be int

        self._channel1.set_endevent(sound_completed_event)

        self._start_playing_message = False
        self._morse_queue = queue.Queue()
        self._setupLogging()

    @staticmethod
    def _setupLogging() -> None:
        root = logging.getLogger()

        # Kick out the default handler
        root.removeHandler(root.handlers[0])

        root.setLevel(logging.DEBUG)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        root.addHandler(handler)

    def run(self):
        logging.info("Display has started")
        self._running = True
        while self._running:
            if self._start_playing_message:  # Flag that we flip if we want to start the sounds
                pygame.event.post(pygame.event.Event(sound_completed_event))
                self._start_playing_message = False
            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    self._running = False
                    break

                if event.type == sound_completed_event:  # The sound that was running has completed.
                    if not self._morse_queue.queue:
                        print("Queue is empty")
                        continue
                    if self._morse_queue.queue[0] == " ":
                        pygame.time.set_timer(pause_between_tick_event,
                                              random.randint(self.MIN_SPACE_PAUSE, self.MAX_SPACE_PAUSE), 1)
                    else:
                        # Set a new event to put some pause between the ticks
                        pygame.time.set_timer(pause_between_tick_event,
                                              random.randint(self.MIN_CHAR_PAUSE, self.MAX_CHAR_PAUSE),
                                              1)

                elif event.type == pause_between_tick_event:
                    # Pause was completed, play the next sound!
                    char_to_play = self._morse_queue.get()
                    if char_to_play == " ":
                        # Post a "fake" sound completed event, this will trigger the next sound to be played.
                        pygame.event.post(pygame.event.Event(sound_completed_event))
                        continue  # We already did the pause, move on!
                    if char_to_play == "-":
                        self._channel1.play(self._click_long)
                    else:
                        self._channel1.play(self._click_short)


def printFinal(img: str):
    # Setup the printer stuff
    p = printer.Usb(0x28e9, 0x0289, out_ep=0x03, profile="ZJ-5870")

    p.image(img)

    # Move the paper a bit so that we have some whitespace to tear it off
    p.control("LF")
    p.control("LF")
    p.control("LF")
    p.control("LF")


# txt = "A short message, oh noes!"


#img = MorseImageCreator.createImage(txt, single_line_config)

#img.save("test.png")


# printFinal("test.png")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--windowed", action="store_true")

    args = parser.parse_args()
    wrapper = PygameWrapper(fullscreen = not args.windowed)

    wrapper.run()
