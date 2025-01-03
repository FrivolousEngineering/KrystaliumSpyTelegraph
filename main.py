import argparse
import logging
from queue import Queue
import sys
import random
import threading
from typing import Optional
import requests

import contextlib

from pygame.event import Event

from PeripheralSerialController import PeripheralSerialController
from Printer import Printer
from SoundController import SoundController
from sql_app.schemas import Target

with contextlib.redirect_stdout(None):
    import pygame

from Config import Config

# Window size
WINDOW_WIDTH = 400
WINDOW_HEIGHT = 400
WINDOW_SURFACE = pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE

DARK_BLUE = (3, 5, 54)

# Pygame events
sound_completed_event = SoundController.sound_completed_event
pause_between_tick_event = pygame.USEREVENT + 2
request_update_server_event = pygame.USEREVENT + 3
retry_printer_not_found_event = pygame.USEREVENT + 4
message_typing_timeout_event = pygame.USEREVENT + 5

multi_line_config = Config("CENTER", 50, 20, 20, 10, 6, add_headers=True)
single_line_config = Config("LEFT", 75, 20, 0, 20, 1, add_headers=False)


class PygameWrapper:
    MIN_SPACE_PAUSE = 400
    MAX_SPACE_PAUSE = 500

    MIN_CHAR_PAUSE = 1
    MAX_CHAR_PAUSE = 1

    REQUEST_UPDATE_TIME = 2000  # 2 sec
    MIN_TIME_BETWEEN_MESSAGES = 10000  # 10 seconds
    RETRY_PRINTER_NOT_FOUND_TIME = 2000  # 2 seconds
    MESSAGE_TYPING_TIMEOUT_TIME = 30000  # 30 secs

    SCREEN_SIZE = (1280, 720)
    SERVER_URL: str = "http://127.0.0.1:8000"

    def __init__(self, fullscreen: bool = True) -> None:
        """
        We are using a wrapper for a few reasons:
        1. We want to handle keyboard inputs from the user (which is suprisingly hard without a simple game engine)
        2. We want to play sounds at certain moments.

        Note that the screen isn't even enabled on the actual device.
        :param fullscreen:
        """
        self._setupLogging()
        pygame.init()

        if fullscreen:
            self._screen = pygame.display.set_mode(self.SCREEN_SIZE, pygame.FULLSCREEN)
        else:
            self._screen = pygame.display.set_mode(self.SCREEN_SIZE)

        self._clock = pygame.time.Clock()
        self._is_running = False  # Is the application still running (used for the main loop)

        self._sound = SoundController()

        self._start_playing_message = False
        self._morse_queue: Queue = Queue()

        self._request_message_to_be_printed_thread: Optional[threading.Thread] = None
        self._request_message_pending = False
        self._last_printed_message_id = None

        self._peripheral_controller = PeripheralSerialController()

        self._typed_text = ""  # The text that is locally typed

        self._printer = Printer()
        self._arm_pos = "Relay"

    def _requestUnprintedMessagesFromServer(self) -> None:
        """
        This will start a thread that will handle the request to the server to ask for unprinted messages.
        :return:
        """
        try:
            if self._request_message_to_be_printed_thread is not None:
                self._request_message_to_be_printed_thread.join()
        except Exception:
            pass
        self._request_message_to_be_printed_thread = threading.Thread(target=self._doServerRequest)
        self._request_message_to_be_printed_thread.start()

    def _doServerRequest(self) -> None:
        try:
            r = requests.get(f"{self.SERVER_URL}/messages/unprinted/")
        except requests.exceptions.ConnectionError:
            logging.error("Failed to connect to the server")
            self._request_message_pending = False
            return
        if r.status_code == 200:
            data = r.json()
            if data:
                logging.info("Message from server obtained")
                if data[0]["type"] == "Morse":
                    for char in data[0]["encoded_text"]:
                        self._morse_queue.put(char)
                self._last_printed_message_id = data[0]["id"]

                self._peripheral_controller.setActiveLed(Target.getIndex(data[0]["target"]))
                self._peripheral_controller.setVoltMeterActive(True)
                self._start_playing_message = True
                # If we got a message from the server that was typed by the players, we only want to play the
                # sounds. We don't want to print the message.
                self._printer.setEnabled(data[0]["direction"] == "Incoming")
            else:
                self._request_message_pending = False
        else:
            logging.error(f"Got non OK status code from server: {r.status_code}")
            self._request_message_pending = False

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

    def _handleKeyDownEvent(self, event: Event):
        # Stop requesting new messages. Players are typing
        self._cancelEvent(request_update_server_event)

        # Start a clearing timer. If we don't, accidental keyboard presses might lock the device.
        # By continuously resetting the timer every time a key is pressed this
        # works as a "x seconds after last activity" timeout.
        self._triggerEvent(message_typing_timeout_event, self.MESSAGE_TYPING_TIMEOUT_TIME)
        if event.key == pygame.K_BACKSPACE:
            if len(self._typed_text) > 0:
                self._typed_text = self._typed_text[:-1]
        elif event.key == pygame.K_RETURN:  # Enter was pressed, send the message to the server
            logging.info(f"Attempting to send the message: {self._typed_text}")
            r = requests.post(f"{self.SERVER_URL}/messages/", json={"text": self._typed_text, "direction": "Outgoing",
                                                                    "target": self._peripheral_controller.getArmPosition()})
            logging.info(f"Sent message with status code {r.status_code}")
            self._request_message_pending = False
            self._typed_text = ""
        else:
            self._typed_text += event.unicode

    @staticmethod
    def _cancelEvent(event_type):
        pygame.time.set_timer(event_type, 0)

    @staticmethod
    def _triggerEvent(event_type, min_time: int, max_time: int = 0) -> None:
        """
        Trigger an event for the pygame loop
        :param event_type:
        :param min_time: The minimum time it should take for this to be triggered.
        :param max_time: The max time that this event should be triggered in. If left to 0, no randomness is aplied and
                            the min_time is leading
        :return:
        """
        time_to_use = random.randint(min_time, max_time) if max_time != 0 else min_time
        pygame.time.set_timer(event_type, time_to_use, loops=1)

    def run(self) -> None:
        logging.info("Display has started")
        self._is_running = True
        self._peripheral_controller.start()
        while self._is_running:
            if self._start_playing_message:  # Flag that we flip if we want to start the sounds
                pygame.event.post(pygame.event.Event(sound_completed_event))
                self._start_playing_message = False

            if not self._request_message_pending:  # We're not waiting for an update from the server
                self._triggerEvent(request_update_server_event, self.REQUEST_UPDATE_TIME)
                self._request_message_pending = True

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    self._handleKeyDownEvent(event)

                if event.type == pygame.QUIT:
                    self._is_running = False
                    break

                if event.type == sound_completed_event or event.type == retry_printer_not_found_event:
                    # The sound that was running has completed or the timeout for failure was hit.
                    if not self._morse_queue.queue:
                        logging.info("Queue is empty")

                        if self._printer.feedPaper():
                            logging.info("Message has been printed!")
                            # Notify the server that the message has been printed
                            requests.post(f"{self.SERVER_URL}/messages/{self._last_printed_message_id}/mark_as_printed")
                            self._sound.playBell()
                            # Disable the LED again!
                            self._peripheral_controller.setActiveLed(-1)
                            self._peripheral_controller.setVoltMeterActive(False)
                            # Only start requesting new messages again after a certain time.
                            # This will ensure that messages don't get mushed together.
                            self._triggerEvent(request_update_server_event, self.MIN_TIME_BETWEEN_MESSAGES)
                        else:
                            # Set an event to try again after some time
                            self._triggerEvent(retry_printer_not_found_event, self.RETRY_PRINTER_NOT_FOUND_TIME)
                        continue
                    if self._morse_queue.queue[0] == " ":
                        self._triggerEvent(pause_between_tick_event, self.MIN_SPACE_PAUSE, self.MAX_SPACE_PAUSE)
                    else:
                        # Set a new event to put some pause between the ticks
                        self._triggerEvent(pause_between_tick_event, self.MIN_CHAR_PAUSE, self.MAX_CHAR_PAUSE)

                elif event.type == pause_between_tick_event:
                    # The pause between sounds has completed. What is the next sound that we have to play?
                    char_to_play = self._morse_queue.get()
                    failed_to_print = False
                    if char_to_play == " ":
                        # Print the message (although we might want to start that when we get the message tho?
                        if self._printer.printSpace():
                            # Post a "fake" sound completed event, this will trigger the next sound to be played.
                            pygame.event.post(pygame.event.Event(sound_completed_event))
                            continue  # We already did the pause, move on!
                        else:
                            failed_to_print = True

                    if char_to_play == "-":
                        if self._printer.printImage("dash.png"):
                            self._sound.playLongClick()
                        else:
                            failed_to_print = True
                    else:
                        if self._printer.printImage("dot.png"):
                            self._sound.playShortClick()
                        else:
                            failed_to_print = True

                    if failed_to_print:
                        logging.warning("Failed to print, scheduling again until printer is back")
                        self._morse_queue.queue.insert(0, char_to_play)
                        # Set an event to try again after some time
                        self._triggerEvent(retry_printer_not_found_event, self.RETRY_PRINTER_NOT_FOUND_TIME)

                elif event.type == request_update_server_event:
                    self._requestUnprintedMessagesFromServer()
                elif event.type == message_typing_timeout_event:
                    logging.info("Typing timeout.")
                    self._typed_text = ""
                    self._request_message_pending = False
        self._peripheral_controller.stop()
        quit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--windowed", action="store_true")

    args = parser.parse_args()
    wrapper = PygameWrapper(fullscreen=not args.windowed)

    wrapper.run()
