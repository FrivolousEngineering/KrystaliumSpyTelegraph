
from escpos import printer

from PIL import Image, ImageDraw, ImageChops, ImageFont, ImageOps

from Config import Config
from MorseImageCreator import MorseImageCreator
from MorseTranslator import MorseTranslator
from SentenceSplitter import SentenceSplitter

PAPER_WIDTH = 384
wide_paper_width = 384
narrow_paper_width = 194




multi_line_config = Config("CENTER", 50, 20, 20, 10, 6, add_headers=True)
single_line_config = Config("LEFT", 75, 20, 20, 20, 1, add_headers=False)

active_configuration = single_line_config





def printFinal(img: str):
    # Setup the printer stuff
    p = printer.Usb(0x28e9, 0x0289, out_ep=0x03, profile="ZJ-5870")

    p.image(img)

    # Move the paper a bit so that we have some whitespace to tear it off
    p.control("LF")
    p.control("LF")
    p.control("LF")
    p.control("LF")



txt = "Lorem ipsum dolor sit amet consectetur adipiscing elit."
txt = "The base has fallen. We do not know who the spy is. Proceed with caution. Trust noone. Death to the iron tzar."

#txt = "A short message, oh noes!"


img = MorseImageCreator.createImage(txt, single_line_config)

img.save("test.png")

#printFinal("test.png")
