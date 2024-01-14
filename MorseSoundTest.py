import contextlib
import queue

from MorseTranslator import MorseTranslator

with contextlib.redirect_stdout(None):
    import pygame

import random

# Window size
WINDOW_WIDTH = 400
WINDOW_HEIGHT = 400
WINDOW_SURFACE = pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE

DARK_BLUE = (3, 5, 54)

sound_completed_event = pygame.USEREVENT + 1
pause_between_tick_event = pygame.USEREVENT + 2

MIN_SPACE_PAUSE = 400
MAX_SPACE_PAUSE = 500

MIN_CHAR_PAUSE = 16
MAX_CHAR_PAUSE = 64

pygame.init()
pygame.mixer.init()
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), WINDOW_SURFACE)

# create separate Channel objects for simultaneous playback
channel1 = pygame.mixer.Channel(0)  # argument must be int

channel1.set_endevent(sound_completed_event)

click_1 = pygame.mixer.Sound("click_short.mp3")
click_2 = pygame.mixer.Sound("click_long.mp3")

clock = pygame.time.Clock()
done = False

text = "Hello world"
morse = MorseTranslator.textToMorse(text)
morse_queue = queue.Queue()
for char in morse:
    morse_queue.put(char)

start_playing_message = True


while not done:
    if start_playing_message:  # Flag that we flip if we want to start the sounds
        pygame.event.post(pygame.event.Event(sound_completed_event))
        start_playing_message = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        elif event.type == sound_completed_event:  # The sound that was running has completed.
            if not morse_queue.queue:
                print("Queue is empty")
                continue
            if morse_queue.queue[0] == " ":
                pygame.time.set_timer(pause_between_tick_event, random.randint(MIN_SPACE_PAUSE, MAX_SPACE_PAUSE), 1)
            else:
                # Set a new event to put some pause between the ticks
                pygame.time.set_timer(pause_between_tick_event, random.randint(MIN_CHAR_PAUSE, MAX_CHAR_PAUSE), 1)

        elif event.type == pause_between_tick_event:
            # Pause was completed, play the next sound!
            char_to_play = morse_queue.get()
            if char_to_play == " ":
                # Post a "fake" sound completed event, this will trigger the next sound to be played.
                pygame.event.post(pygame.event.Event(sound_completed_event))
                continue  # We already did the pause, move on!
            if char_to_play == "-":
                channel1.play(click_1)
            else:
                channel1.play(click_2)

    # Update the display (ok, we don't need any, but whatever)
    window.fill(DARK_BLUE)
    pygame.display.flip()

    # Clamp FPS
    clock.tick_busy_loop(60)

pygame.quit()
