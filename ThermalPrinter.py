# *************************************************************************
# This is a Python library for the Adafruit Thermal Printer.
# Pick one up at --> http://www.adafruit.com/products/597
# These printers use TTL serial to communicate, 2 pins are required.
# IMPORTANT: On 3.3V systems (e.g. Raspberry Pi), use a 10K resistor on
# the RX pin (TX on the printer, green wire), or simply leave unconnected.
#
# Adafruit invests time and resources providing this open source code.
# Please support Adafruit and open-source hardware by purchasing products
# from Adafruit!
#
# Written by Limor Fried/Ladyada for Adafruit Industries.
# Python port by Phil Burgess for Adafruit Industries.
# MIT license, all text above must be included in any redistribution.
# *************************************************************************

# This is pretty much a 1:1 direct Python port of the Adafruit_Thermal
# library for Arduino.  All methods use the same naming conventions as the
# Arduino library, with only slight changes in parameter behavior where
# needed.  This should simplify porting existing Adafruit_Thermal-based
# printer projects to Raspberry Pi, BeagleBone, etc.  See printertest.py
# for an example.
#
# One significant change is the addition of the printImage() function,
# which ties this to the Python Imaging Library and opens the door to a
# lot of cool graphical stuff!
#
# TO DO:
# - Might use standard ConfigParser library to put thermal calibration
#   settings in a global configuration file (rather than in the library).
# - Make this use proper Python library installation procedure.
# - Trap errors properly.  Some stuff just falls through right now.
# - Add docstrings throughout!

# Python 2.X code using the library usu. needs to include the next line:
from __future__ import print_function
from serial import Serial
import time
import os
import sys
from threading import Lock


class ThermalPrinter(Serial):
    resumeTime = 0.0
    byteTime = 0.0
    dotPrintTime = 0.0
    dotFeedTime = 0.0
    prevByte = '\n'
    column = 0
    maxColumn = 32
    charHeight = 24
    lineSpacing = 8
    barcodeHeight = 50
    printMode = 0
    defaultHeatTime = 160
    firmwareVersion = 268
    writeToStdout = False

    def __init__(self, port, baudrate=9600, *args, **kwargs):
        os.system("/home/pi/polapi2/rpirtscts.sh")
        Serial.__init__(self, port, baudrate, *args, **kwargs)
        # self.wake()
        self.reset()
        self.initialHeattime = 180

    def setPrintSettings(self, heatdot=5, heattime=180, heatinterval=200):  # heatime=120
        self.writeBytes(
            27,  # Esc
            55,  # 7 (print settings)
            heatdot,  # Heat dots
            heattime,  # Lib default
            heatinterval)  # Heat interval

    def setPrintDensity(self, density=12, breaktime=7):
        self.writeBytes(
            18,  # DC2
            35,  # Print density
            (breaktime << 5) | density)

    # 'Raw' byte-writing method
    def writeBytes(self, *args):
        for arg in args:
            super(ThermalPrinter, self).write(chr(arg))

    # Override write() method to keep track of paper feed.
    def write(self, *data):
        for i in range(len(data)):
            c = data[i]
            if c == 0x13:
                continue
            super(ThermalPrinter, self).write(c)
            if ((c == '\n') or (self.column == self.maxColumn)):
                # Newline or wrap
                if self.prevByte != '\n':
                    self.column = 0
                    c = '\n'
            else:
                self.column += 1
            self.prevByte = c

    def reset(self):
        self._reset = True
        time.sleep(0.1)
        self.writeBytes(27, 64)  # Esc @ = init command
        self.prevByte = '\n'  # Treat as if prior line is blank
        self.column = 0
        self.maxColumn = 32
        self.charHeight = 24
        self.lineSpacing = 6
        self.barcodeHeight = 50
        if self.firmwareVersion >= 264:
            # Configure tab stops on recent printers
            self.writeBytes(27, 68)  # Set tab stops
            self.writeBytes(4, 8, 12, 16)  # every 4 columns,
            self.writeBytes(20, 24, 28, 0)  # 0 is end-of-list.
        self.setPrintSettings()
        self.setPrintDensity()
        time.sleep(0.1)
        self._reset = False

    # Reset text formatting parameters.
    def setDefault(self):
        self.online()
        self.justify('L')
        self.inverseOff()
        self.doubleHeightOff()
        self.setLineHeight(30)
        self.boldOff()
        self.underlineOff()
        self.setSize('s')
        self.setCharset()
        self.setCodePage()

    def test(self):
        self.write("Hello world!")
        self.feed(2)

    def testPage(self):
        self.writeBytes(18, 84)

    def setPrintMode(self, mask):
        self.printMode |= mask
        self.writePrintMode()
        if self.printMode & self.DOUBLE_HEIGHT_MASK:
            self.charHeight = 48
        else:
            self.charHeight = 24
        if self.printMode & self.DOUBLE_WIDTH_MASK:
            self.maxColumn = 16
        else:
            self.maxColumn = 32

    def unsetPrintMode(self, mask):
        self.printMode &= ~mask
        self.writePrintMode()
        if self.printMode & self.DOUBLE_HEIGHT_MASK:
            self.charHeight = 48
        else:
            self.charHeight = 24
        if self.printMode & self.DOUBLE_WIDTH_MASK:
            self.maxColumn = 16
        else:
            self.maxColumn = 32

    def writePrintMode(self):
        self.writeBytes(27, 33, self.printMode)

    def normal(self):
        self.printMode = 0
        self.writePrintMode()

    def inverseOn(self):
        self.writeBytes(29, 66, 1)

    def inverseOff(self):
        self.writeBytes(29, 66, 0)

    def upsideDownOn(self):
        self.setPrintMode(self.UPDOWN_MASK)

    def upsideDownOff(self):
        self.unsetPrintMode(self.UPDOWN_MASK)

    def doubleHeightOn(self):
        self.setPrintMode(self.DOUBLE_HEIGHT_MASK)

    def doubleHeightOff(self):
        self.unsetPrintMode(self.DOUBLE_HEIGHT_MASK)

    def doubleWidthOn(self):
        self.setPrintMode(self.DOUBLE_WIDTH_MASK)

    def doubleWidthOff(self):
        self.unsetPrintMode(self.DOUBLE_WIDTH_MASK)

    def strikeOn(self):
        self.setPrintMode(self.STRIKE_MASK)

    def strikeOff(self):
        self.unsetPrintMode(self.STRIKE_MASK)

    def boldOn(self):
        self.setPrintMode(self.BOLD_MASK)

    def boldOff(self):
        self.unsetPrintMode(self.BOLD_MASK)

    def justify(self, value):
        c = value.upper()
        if c == 'C':
            pos = 1
        elif c == 'R':
            pos = 2
        else:
            pos = 0
        self.writeBytes(0x1B, 0x61, pos)

    # Feeds by the specified number of lines
    def feed(self, x=1):
        self.writeBytes(27, 100, x)
        self.prevByte = '\n'
        self.column = 0

    # Feeds by the specified number of individual pixel rows
    def feedRows(self, rows):
        self.writeBytes(27, 74, rows)
        self.prevByte = '\n'
        self.column = 0

    def flush(self):
        self.writeBytes(12)  # ASCII FF

    def setSize(self, value):
        c = value.upper()
        if c == 'L':  # Large: double width and height
            size = 0x11
            self.charHeight = 48
            self.maxColumn = 16
        elif c == 'M':  # Medium: double height
            size = 0x01
            self.charHeight = 48
            self.maxColumn = 32
        else:  # Small: standard width and height
            size = 0x00
            self.charHeight = 24
            self.maxColumn = 32

        self.writeBytes(29, 33, size)
        prevByte = '\n'  # Setting the size adds a linefeed

    # Underlines of different weights can be produced:
    # 0 - no underline
    # 1 - normal underline
    # 2 - thick underline
    def underlineOn(self, weight=1):
        if weight > 2:
            weight = 2
        self.writeBytes(27, 45, weight)

    def underlineOff(self):
        self.writeBytes(27, 45, 0)

    def toBitmap(self, image):
        if image.mode != '1':
            image = image.convert('1')

        width = image.size[0]
        height = image.size[1]
        if width > 384:
            width = 384
        rowBytes = (width + 7) / 8
        bitmap = bytearray(rowBytes * height)
        pixels = image.load()

        for y in range(height):
            n = y * rowBytes
            x = 0
            for b in range(rowBytes):
                sum = 0
                bit = 128
                while bit > 0:
                    if x >= width:
                        break
                    if pixels[x, y] == 0:
                        sum |= bit
                    x += 1
                    bit >>= 1
                bitmap[n + b] = sum
        return bitmap

    def printImage(self, image, LaaT=False):
        # self.reset()
        if self.initialHeattime > 120:
            # self.setPrintSettings(self.initialHeattime)
            self.initialHeattime -= 20
        self.printBitmap(
            image.size[0],
            image.size[1],
            self.toBitmap(image),
            LaaT)

    def streamImage(self, streamer):
        # self.reset()
        data = streamer.get()
        total_raw = 0
        while data:
            nb_row = streamer.nb_image - total_raw
            if nb_row > 255:
                nb_row = 255
            self.writeBytes(18, 42, nb_row, 48)
            for i in range(nb_row):
                start = time.time()
                bmp = self.toBitmap(data)
                for j in range(48):
                    super(ThermalPrinter, self).write(chr(bmp[j]))
                data = streamer.get()
            total_raw += nb_row

    def printBitmap(self, w, h, bitmap, LaaT=False):
        rowBytes = (w + 7) / 8  # Round up to next byte boundary
        if rowBytes >= 48:
            rowBytesClipped = 48  # 384 pixels max width
        else:
            rowBytesClipped = rowBytes

        # if LaaT (line-at-a-time) is True, print bitmaps
        # scanline-at-a-time (rather than in chunks).
        # This tends to make for much cleaner printing
        # (no feed gaps) on large images...but has the
        # opposite effect on small images that would fit
        # in a single 'chunk', so use carefully!
        if LaaT:
            maxChunkHeight = 1
        else:
            maxChunkHeight = 255

        i = 0
        for rowStart in range(0, h, maxChunkHeight):
            chunkHeight = h - rowStart
            if chunkHeight > maxChunkHeight:
                chunkHeight = maxChunkHeight

            # Timeout wait happens here
            self.writeBytes(18, 42, chunkHeight, rowBytesClipped)
            # sleeptime = 0.05
            for y in range(chunkHeight):
                # blackdotbit = 0
                for x in range(rowBytesClipped):
                    if self._reset:
                        return
                    if self.writeToStdout:
                        sys.stdout.write(
                            chr(bitmap[i]))
                    else:
                        super(ThermalPrinter,
                              self).write(chr(bitmap[i]))
                        # blackdotbit += bin(bitmap[i])[2:].count('1')
                    i += 1
                i += rowBytes - rowBytesClipped
                # sleep = ((float(blackdotbit) / 48)**3) * 1700
                # sleeptime += sleep / 10000000
                # if sleeptime > 0.5:
                #    time.sleep(sleeptime)
                #    sleeptime = 0

        self.prevByte = '\n'
        print('finish printing')

    # Take the printer offline. Print commands sent after this
    # will be ignored until 'online' is called.
    def offline(self):
        self.writeBytes(27, 61, 0)

    # Take the printer online. Subsequent print commands will be obeyed.
    def online(self):
        self.writeBytes(27, 61, 1)

    # Put the printer into a low-energy state immediately.
    def sleep(self):
        self.sleepAfter(1)  # Can't be 0, that means "don't sleep"

    # Put the printer into a low-energy state after
    # the given number of seconds.
    def sleepAfter(self, seconds):
        self.writeBytes(27, 56, 0)
        self.writeBytes(27, 56, seconds & 0xFF, seconds >> 8)

    def wake(self):
        self.writeBytes(255)
        time.sleep(0.05)  # 50 ms
        self.writeBytes(27, 118, 0)  # Sleep off (important!)

    # Check the status of the paper using the printers self reporting
    # ability. Doesn't match the datasheet...
    # Returns True for paper, False for no paper.
    def hasPaper(self):
        self.writeBytes(27, 118, 255)
        # Bit 2 of response seems to be paper status
        stat = ord(self.read(1)) & 0b00000100
        # If set, we have paper; if clear, no paper
        return stat == 0

    def setLineHeight(self, val=32):
        if val < 24:
            val = 24
        self.lineSpacing = val - 24

        # The printer doesn't take into account the current text
        # height when setting line height, making this more akin
        # to inter-line spacing.  Default line spacing is 32
        # (char height of 24, line spacing of 8).
        self.writeBytes(27, 51, val)

    CHARSET_USA = 0
    CHARSET_FRANCE = 1
    CHARSET_GERMANY = 2
    CHARSET_UK = 3
    CHARSET_DENMARK1 = 4
    CHARSET_SWEDEN = 5
    CHARSET_ITALY = 6
    CHARSET_SPAIN1 = 7
    CHARSET_JAPAN = 8
    CHARSET_NORWAY = 9
    CHARSET_DENMARK2 = 10
    CHARSET_SPAIN2 = 11
    CHARSET_LATINAMERICA = 12
    CHARSET_KOREA = 13
    CHARSET_SLOVENIA = 14
    CHARSET_CROATIA = 14
    CHARSET_CHINA = 15

    # Alters some chars in ASCII 0x23-0x7E range; see datasheet
    def setCharset(self, val=0):
        if val > 15:
            val = 15
        self.writeBytes(27, 82, val)

    CODEPAGE_CP437 = 0  # USA, Standard Europe
    CODEPAGE_KATAKANA = 1
    CODEPAGE_CP850 = 2  # Multilingual
    CODEPAGE_CP860 = 3  # Portuguese
    CODEPAGE_CP863 = 4  # Canadian-French
    CODEPAGE_CP865 = 5  # Nordic
    CODEPAGE_WCP1251 = 6  # Cyrillic
    CODEPAGE_CP866 = 7  # Cyrillic #2
    CODEPAGE_MIK = 8  # Cyrillic/Bulgarian
    CODEPAGE_CP755 = 9  # East Europe, Latvian 2
    CODEPAGE_IRAN = 10
    CODEPAGE_CP862 = 15  # Hebrew
    CODEPAGE_WCP1252 = 16  # Latin 1
    CODEPAGE_WCP1253 = 17  # Greek
    CODEPAGE_CP852 = 18  # Latin 2
    CODEPAGE_CP858 = 19  # Multilingual Latin 1 + Euro
    CODEPAGE_IRAN2 = 20
    CODEPAGE_LATVIAN = 21
    CODEPAGE_CP864 = 22  # Arabic
    CODEPAGE_ISO_8859_1 = 23  # West Europe
    CODEPAGE_CP737 = 24  # Greek
    CODEPAGE_WCP1257 = 25  # Baltic
    CODEPAGE_THAI = 26
    CODEPAGE_CP720 = 27  # Arabic
    CODEPAGE_CP855 = 28
    CODEPAGE_CP857 = 29  # Turkish
    CODEPAGE_WCP1250 = 30  # Central Europe
    CODEPAGE_CP775 = 31
    CODEPAGE_WCP1254 = 32  # Turkish
    CODEPAGE_WCP1255 = 33  # Hebrew
    CODEPAGE_WCP1256 = 34  # Arabic
    CODEPAGE_WCP1258 = 35  # Vietnam
    CODEPAGE_ISO_8859_2 = 36  # Latin 2
    CODEPAGE_ISO_8859_3 = 37  # Latin 3
    CODEPAGE_ISO_8859_4 = 38  # Baltic
    CODEPAGE_ISO_8859_5 = 39  # Cyrillic
    CODEPAGE_ISO_8859_6 = 40  # Arabic
    CODEPAGE_ISO_8859_7 = 41  # Greek
    CODEPAGE_ISO_8859_8 = 42  # Hebrew
    CODEPAGE_ISO_8859_9 = 43  # Turkish
    CODEPAGE_ISO_8859_15 = 44  # Latin 3
    CODEPAGE_THAI2 = 45
    CODEPAGE_CP856 = 46
    CODEPAGE_CP874 = 47

    # Selects alt symbols for 'upper' ASCII values 0x80-0xFF
    def setCodePage(self, val=0):
        if val > 47:
            val = 47
        self.writeBytes(27, 116, val)

    # Copied from Arduino lib for parity; may not work on all printers
    def tab(self):
        self.writeBytes(9)
        self.column = (self.column + 4) & 0xFC

    # Copied from Arduino lib for parity; may not work on all printers
    def setCharSpacing(self, spacing):
        self.writeBytes(27, 32, spacing)

    # Overloading print() in Python pre-3.0 is dirty pool,
    # but these are here to provide more direct compatibility
    # with existing code written for the Arduino library.
    def printe(self, *args, **kwargs):
        for arg in args:
            self.write(str(arg))

    # For Arduino code compatibility again
    def println(self, *args, **kwargs):
        for arg in args:
            self.write(str(arg))
        self.write('\n')
