from escpos.exceptions import DeviceNotFoundError
from escpos import printer
from usb.core import USBError
import logging
import subprocess
import struct
import fcntl
import os

USBLP_GET_STATUS = 0x060b


def runningAsRoot() -> bool:
    return os.getuid() == 0


class Printer:
    def __init__(self) -> None:
        """
        Wrapper around the USB thermal printer. Handles things like being disabled and re-creating the device
        if the connection was lost.
        """
        self._printer: printer.Usb = self._createPrinter()
        self._should_print: bool = True

    def setEnabled(self, enabled: bool) -> None:
        self._should_print = enabled

    @staticmethod
    def _createPrinter() -> printer.Usb:
        return printer.Usb(0x28e9, 0x0289, out_ep=0x03, profile="ZJ-5870")

    @staticmethod
    def _forceResetUSBPrinter():
        subprocess.run(["sudo", "rmmod", "usblp"])
        subprocess.run(["sudo", "modprobe", "usblp"])
        subprocess.run(["sudo", "chmod", "666", "/dev/usb/lp1"])


    def feedSingle(self):
        if not self._should_print:
            return True
        # Move the paper a bit so that we have some whitespace to tear it off
        if not self.hasPaper():
            return False
        try:
            self._printer.control("LF")
            return True
        except (DeviceNotFoundError, USBError):
            self._printer = self._createPrinter()
            return False
    def feedPaper(self) -> bool:
        if not self._should_print:
            return True
        # Move the paper a bit so that we have some whitespace to tear it off
        if not self.hasPaper():
            return False
        try:
            self._printer.control("LF")
            self._printer.control("LF")
            self._printer.control("LF")
            self._printer.control("LF")
            return True
        except (DeviceNotFoundError, USBError):
            self._printer = self._createPrinter()
            return False

    def printSpace(self) -> bool:
        if not self._should_print:
            return True

        if not self.hasPaper():
            return False
        try:
            self._printer.control("LF")
            return True
        except (DeviceNotFoundError, USBError):
            logging.warning("printer not found")
            self._printer = self._createPrinter()
            return False

    def printImage(self, img: str) -> bool:
        if not self._should_print:
            return True
        if not self.hasPaper():
            return False
        try:
            self._printer.image(img)
            return True
        except (DeviceNotFoundError, USBError):
            logging.warning("printer not found while printing image")
            self._printer = self._createPrinter()
            return False

    def printSingleLineText(self, line: str) -> bool:
        if not self._should_print:
            return True
        if not self.hasPaper():
            return False
        try:
            self._printer.set(bold=True)
            self._printer.text(line)
            self._printer.control("LF")
            return True
        except (DeviceNotFoundError, USBError):
            logging.warning("printer not found while printing text")
            self._printer = self._createPrinter()
            return False

    def printGridTextLine(self, line: str) -> bool:
        if not self._should_print:
            return True
        if not self.hasPaper():
            return False
        try:
            self._printer.set(bold=True)
            # Ensure we use double spaces
            text_to_print = line.replace(" ", "  ")
            # And print with 2 spaces in front of if (for spacing)
            self._printer.text(f"  {text_to_print}")
            self._printer.control("LF")
            return True
        except (DeviceNotFoundError, USBError):
            logging.warning("printer not found while printing text")
            self._printer = self._createPrinter()
            return False


    def hasPaper(self):
        if not runningAsRoot():
            # This check will only work if you are running as root.
            logging.warning("Unable to check paper status, not running as root")
            return True
        # Story time! The escpos library doesn't handle the paper checking correctly. For some reason the default
        # usb printing driver does. But that driver doesn't play well if i want to send images. So, as any "sane"
        # developer, it makes me think "Well, why not create a monster of frankenstein".
        # But the problem with monsters are is that they start shouting "WHY HAVE YOU CREATED ME FATHER"
        # That is where the resetUsbPrinter comes in.
        # Every time we send any command over USB to the printer via escpos, the linux kernel is very graceful with
        # removing the /dev/usb/lp1. The only way to get it back is, you guessed it, restart the module
        # May god have mercy on my soul, for these sins should not give me any.
        try:
            self._forceResetUSBPrinter()
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
