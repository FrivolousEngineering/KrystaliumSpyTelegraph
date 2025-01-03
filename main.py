import argparse
import logging
from queue import Queue
import sys
import random
import threading
from typing import Optional
import os
import requests
import fcntl
import struct
import subprocess



from escpos import printer
import contextlib

from escpos.exceptions import DeviceNotFoundError
from usb.core import USBError

from PeripheralSerialController import PeripheralSerialController
from sql_app.schemas import Target

with contextlib.redirect_stdout(None):
    import pygame

from Config import Config
from MorseImageCreator import MorseImageCreator

# Window size
WINDOW_WIDTH = 400
WINDOW_HEIGHT = 400
WINDOW_SURFACE = pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE
USBLP_GET_STATUS = 0x060b
DARK_BLUE = (3, 5, 54)

# Pygame events
sound_completed_event = pygame.USEREVENT + 1
pause_between_tick_event = pygame.USEREVENT + 2
request_update_server_event = pygame.USEREVENT + 3
retry_printer_not_found_event = pygame.USEREVENT + 4
message_typing_timeout_event = pygame.USEREVENT + 5

multi_line_config = Config("CENTER", 50, 20, 20, 10, 6, add_headers=True)
single_line_config = Config("LEFT", 75, 20, 0, 20, 1, add_headers=False)


def runningAsRoot() -> bool:
    return os.getuid() == 0


class PygameWrapper:
    MIN_SPACE_PAUSE = 400
    MAX_SPACE_PAUSE = 500

    MIN_CHAR_PAUSE = 1
    MAX_CHAR_PAUSE = 1

    REQUEST_UPDATE_TIME = 2000  # 2 sec
    MIN_TIME_BETWEEN_MESSAGES = 10000  # 10 seconds
    RETRY_PRINTER_NOT_FOUND_TIME = 2000  # 2 seconds
    MESSAGE_TYPING_TIMEOUT_TIME = 30000  # 30 secs

    def __init__(self, fullscreen: bool = True) -> None:
        pygame.init()
        self._screen_width = 1280
        self._screen_height = 720
        if fullscreen:
            self._screen = pygame.display.set_mode((self._screen_width, self._screen_height), pygame.FULLSCREEN)
        else:
            self._screen = pygame.display.set_mode((self._screen_width, self._screen_height))
        self._clock = pygame.time.Clock()
        self._running = False

        self._base_server_url: str = "http://127.0.0.1:8000"
        pygame.mixer.init()
        self._click_short = pygame.mixer.Sound("click_short.mp3")
        self._click_long = pygame.mixer.Sound("click_long.mp3")
        self._final_bell = pygame.mixer.Sound("final_bell.mp3")

        self._channel1 = pygame.mixer.Channel(0)
        self._channel2 = pygame.mixer.Channel(1)  # Used for the final bell, as we don't want a sound complete event

        self._channel1.set_endevent(sound_completed_event)

        self._start_playing_message = False
        self._morse_queue: Queue = Queue()
        self._setupLogging()
        self._request_message_to_be_printed_thread: Optional[threading.Thread] = None
        self._request_message_pending = False
        self._last_printed_message_id = None

        self._peripheral_controller = PeripheralSerialController()

        self._typed_text = ""  # The text that is localy typed

        self._printer = self.createPrinter()
        self._arm_pos = "Relay"
        self._should_print = True

    @staticmethod
    def createPrinter() -> printer.Usb:
        return printer.Usb(0x28e9, 0x0289, out_ep=0x03, profile="ZJ-5870")

    @staticmethod
    def resetUsbPrinter():
        subprocess.run(["sudo", "rmmod", "usblp"])
        subprocess.run(["sudo", "modprobe", "usblp"])
        subprocess.run(["sudo", "chmod", "666", "/dev/usb/lp1"])

    @staticmethod
    def hasPaper():
        if not runningAsRoot():
            # This check will only work if you are running as root.
            logging.warning("Unable to check paper status, not running as root")
            return
        # Story time! The escpos library doesn't handle the paper checking correctly. For some reason the default
        # usb printing driver does. But that driver doesn't play well if i want to send images. So, as any "sane"
        # developer, it makes me think "Well, why not create a monster of frankenstein".
        # But the problem with monsters are is that they start shouting "WHY HAVE YOU CREATED ME FATHER"
        # That is where the resetUsbPrinter comes in.
        # Every time we send any command over USB to the printer via escpos, the linux kernel is very graceful with
        # removing the /dev/usb/lp1. The only way to get it back is, you guessed it, restart the module
        # May god have mercy on my soul, for these sins should not give me any.
        try:
            PygameWrapper.resetUsbPrinter()
            with open("/dev/usb/lp1", "r+b") as printer:
                # Send paper status command
                printer.write(b'\x10\x04\x04')
                printer.flush()

                # Get status using ioctl
                status = struct.unpack('B', fcntl.ioctl(printer, USBLP_GET_STATUS, b'\x00'))[0]
                result = f"{status:08b}"  # Convert status to binary
                paper_present = result[2] == "1"  # Check paper bit

                # Graceful close: Reset printer to avoid device lock
                # printer.write(b'\x1b\x40')  # ESC @ (reset command)
                # printer.flush()

                return paper_present
        except FileNotFoundError:
            print("Printer not found at /dev/usb/lp1.")
            return False
        except Exception as e:
            print("Error reading printer status:", e)
            return False

    def _requestMessageToBePrinted(self) -> None:
        try:
            if self._request_message_to_be_printed_thread is not None:
                self._request_message_to_be_printed_thread.join()
        except Exception:
            pass
        self._request_message_to_be_printed_thread = threading.Thread(target = self._doServerRequest)
        self._request_message_to_be_printed_thread.start()

    def _doServerRequest(self) -> None:
        try:
            r = requests.get(f"{self._base_server_url}/messages/unprinted/")
        except requests.exceptions.ConnectionError:
            logging.error("Failed to connect to the server")
            self._request_message_pending = False
            return
        if r.status_code == 200:
            data = r.json()

            if data:
                for char in data[0]["morse"]:
                    self._morse_queue.put(char)
                self._last_printed_message_id = data[0]["id"]
                # Create the image to print and store it
                image = MorseImageCreator.createImage(data[0]["text"], single_line_config)
                image.save(f"{self._last_printed_message_id}.png")
                self._peripheral_controller.setActiveLed(Target.getIndex(data[0]["target"]))
                self._peripheral_controller.setVoltMeterActive(True)
                self._start_playing_message = True
                self._should_print = data[0]["direction"] == "Incoming"
            else:
                self._request_message_pending = False
        else:
            self._request_message_pending = False

    def printImage(self, img: str) -> bool:
        if not self._should_print:
            return True

        try:
            self._printer.image(img)
            return True
        except (DeviceNotFoundError, USBError):
            logging.warning("printer not found")
            self._printer = self.createPrinter()
            return False

    def feedPaper(self) -> bool:
        # Move the paper a bit so that we have some whitespace to tear it off
        try:
            self._printer.control("LF")
            self._printer.control("LF")
            self._printer.control("LF")
            self._printer.control("LF")
            return True
        except (DeviceNotFoundError, USBError):
            self._printer = self.createPrinter()
            return False

    def printSpace(self) -> bool:
        if not self._should_print:
            return True
        try:
            self._printer.control("LF")
            return True
        except (DeviceNotFoundError, USBError):
            logging.warning("printer not found")
            self._printer = self.createPrinter()
            return False

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

    def run(self) -> None:
        logging.info("Display has started")
        self._running = True
        self._peripheral_controller.start()
        while self._running:
            if self._start_playing_message:  # Flag that we flip if we want to start the sounds
                pygame.event.post(pygame.event.Event(sound_completed_event))
                self._start_playing_message = False

            if not self._request_message_pending:  # Request update from server
                pygame.time.set_timer(request_update_server_event, self.REQUEST_UPDATE_TIME, 1)
                self._request_message_pending = True

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    # Stop requesting new messages. Players are typing
                    pygame.time.set_timer(request_update_server_event, 0)

                    # Start a clearing timer (otherwise if someone accidentally touches the keyboard, the entire
                    # thing stops working. By continiously resetting the timer every time a key is pressed this
                    # works as a "x seconds after last activity" timeout.
                    pygame.time.set_timer(message_typing_timeout_event, self.MESSAGE_TYPING_TIMEOUT_TIME, 1)
                    if event.key == pygame.K_BACKSPACE:
                        if len(self._typed_text) > 0:
                            self._typed_text = self._typed_text[:-1]
                    elif event.key == pygame.K_RETURN:
                        logging.info(f"Attempting to send the message: {self._typed_text}")
                        r = requests.post(f"{self._base_server_url}/messages/", json = {"text": self._typed_text, "direction": "Outgoing", "target": self._peripheral_controller.getArmPosition()})
                        logging.info(f"Sent message with status code {r.status_code}")
                        self._request_message_pending = False
                        self._typed_text = ""
                    else:
                        self._typed_text += event.unicode

                if event.type == pygame.QUIT:
                    self._running = False
                    break

                if event.type == sound_completed_event or event.type == retry_printer_not_found_event:
                    # The sound that was running has completed or the timeout for failure was hit.
                    if not self._morse_queue.queue:
                        logging.info("Queue is empty")

                        if self.feedPaper():
                            logging.info("Message has been printed!")
                            # Notify the server that the message has been printed
                            requests.post(f"{self._base_server_url}/messages/{self._last_printed_message_id}/mark_as_printed")
                            self._channel2.queue(self._final_bell)
                            # Disable the led again!
                            self._peripheral_controller.setActiveLed(-1)
                            self._peripheral_controller.setVoltMeterActive(False)
                            # Only start requesting new messages again after a certain time.
                            # This will ensure that messages don't get mushed together.
                            pygame.time.set_timer(request_update_server_event, self.MIN_TIME_BETWEEN_MESSAGES, 1)
                        else:
                            # Set an event to try again after some time
                            pygame.time.set_timer(retry_printer_not_found_event, self.RETRY_PRINTER_NOT_FOUND_TIME, 1)
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
                    failed_to_print = False
                    if char_to_play == " ":
                        # Print the message (although we might want to start that when we get the message tho?
                        if self.printSpace():
                            # Post a "fake" sound completed event, this will trigger the next sound to be played.
                            pygame.event.post(pygame.event.Event(sound_completed_event))
                            continue  # We already did the pause, move on!
                        else:
                            failed_to_print = True

                    if char_to_play == "-":
                        if self.printImage("dash.png"):
                            self._channel1.queue(self._click_long)
                        else:
                            failed_to_print = True
                    else:
                        if self.printImage("dot.png"):
                            self._channel1.queue(self._click_short)
                        else:
                            failed_to_print = True

                    if failed_to_print:
                        logging.warning("Failed to print, scheduling again untill printer is back")
                        self._morse_queue.queue.insert(0, char_to_play)
                        # Set an event to try again after some time
                        pygame.time.set_timer(retry_printer_not_found_event, self.RETRY_PRINTER_NOT_FOUND_TIME, 1)

                elif event.type == request_update_server_event:
                    self._requestMessageToBePrinted()
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
