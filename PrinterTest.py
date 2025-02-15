import fcntl
import struct
import os
import time


USBLP_GET_STATUS = 0x060b

from escpos import printer as escposPrinter
import subprocess


def resetUsbPrinter():
    subprocess.run(["sudo", "rmmod", "usblp"])
    subprocess.run(["sudo", "modprobe", "usblp"])
    subprocess.run(["sudo", "chmod", "666", "/dev/usb/lp1"])


def hasPaper():
    try:
        # Story time! The escpos library doesn't handle the paper checking correctly. For some reason the default
        # usb printing driver does. But that driver doesn't play well if i want to send images. So, as any "sane"
        # developer, it makes me think "Well, why not create a monster of frankenstein".
        # But the problem with monsters are is that they start shouting "WHY HAVE YOU CREATED ME FATHER"
        # That is where the resetUsbPrinter comes in.
        # Every time we send any command over USB to the printer via escpos, the linux kernel is very graceful with
        # removing the /dev/usb/lp1. The only way to get it back is, you guessed it, restart the module
        # May god have mercy on my soul, for these sins should not give me any.
        resetUsbPrinter()
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





p = escposPrinter.Usb(0x28e9, 0x0289, out_ep=0x03, profile="ZJ-5870")
p.image("Divider.png")

#reset_usb_printer()
#status = p.device.read(p.in_ep)
#print(status)

