
from escpos import printer

from PIL import Image, ImageDraw, ImageChops, ImageFont, ImageOps

from MorseTranslator import MorseTranslator
from SentenceSplitter import SentenceSplitter

PAPER_WIDTH = 384
wide_paper_width = 384
narrow_paper_width = 194

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


class Config:

    def __init__(self, text_alignment, font_size, line_spacing, text_margin, text_offset, num_lines, add_headers):
        self.text_alignment: str = text_alignment

        self.font_size = font_size
        self.line_spacing = line_spacing
        self.text_margin = text_margin
        self.text_offset = text_offset  # Since we use dots, it makes the text seem not centered otherwise.
        self.num_lines = num_lines
        self.add_header = add_headers


multi_line_config = Config("CENTER", 50, 20, 20, 10, 6, add_headers=True)
single_line_config = Config("LEFT", 75, 20, 20, 20, 1, add_headers=False)

active_configuration = single_line_config


def trim(image):
    inverted_image = image.convert("RGB")
    inverted_image = ImageOps.invert(inverted_image)
    return image.crop(inverted_image.getbbox())


def addMargin(image, top, right, bottom, left, color):
    width, height = image.size
    new_width = width + right + left
    new_height = height + top + bottom
    result = Image.new(image.mode, (new_width, new_height), color)
    result.paste(image, (left, top))
    return result


def custom_split(input_string, max_splits):
    words = input_string.split()
    result = []
    max_letters_per_split = len(input_string) // max_splits
    while len(words) > 0 and len(result) < max_splits - 1:
        current_split = words.pop(0)
        while len(words) > 0 and len(current_split) + len(words[0]) + 1 <= max_letters_per_split:
            current_split += " " + words.pop(0)

        result.append(current_split)

    if len(words) > 0:
        result.append(" ".join(words))

    return result


def cutStringIntoParts(input_string, num_parts):
    words = input_string.split()
    total_words = len(words)

    # Calculate the number of words in each part and the remaining words
    words_per_part = total_words // num_parts
    remaining_words = total_words % num_parts

    # Initialize a list to store the parts
    parts = []

    # Iterate through each part
    start_index = 0
    for i in range(num_parts):
        # Calculate the end index for the current part
        end_index = start_index + words_per_part + (1 if i < remaining_words else 0)

        # Extract the current part and join the words
        current_part = ' '.join(words[start_index:end_index])

        # Add the current part to the list
        parts.append(current_part)

        # Update the start index for the next part
        start_index = end_index

    return parts


def concatImageVertical(im1, im2):
    dst = Image.new('RGB', (im1.width, im1.height + im2.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (0, im1.height))
    return dst


def drawRotatedText(image, angle, xy, text, fill, *args, **kwargs):
    """ Draw text at an angle into an image, takes the same arguments
        as Image.text() except for:

    :param image: Image to write text into
    :param angle: Angle to write text at
    """
    # get the size of our image
    width, height = image.size
    max_dim = max(width, height)

    # build a transparency mask large enough to hold the text
    mask_size = (max_dim * 2, max_dim * 2)
    mask = Image.new('L', mask_size, 0)

    # add text to mask
    draw = ImageDraw.Draw(mask)
    draw.text((max_dim, max_dim), text, 255, *args, **kwargs)

    if angle % 90 == 0:
        # rotate by multiple of 90 deg is easier
        rotated_mask = mask.rotate(angle)
    else:
        # rotate an an enlarged mask to minimize jaggies
        bigger_mask = mask.resize((max_dim*8, max_dim*8),
                                  resample=Image.BICUBIC)
        rotated_mask = bigger_mask.rotate(angle).resize(
            mask_size, resample=Image.LANCZOS)

    # crop the mask to match image
    mask_xy = (max_dim - xy[0], max_dim - xy[1])
    b_box = mask_xy + (mask_xy[0] + width, mask_xy[1] + height)
    mask = rotated_mask.crop(b_box)

    # paste the appropriate color, with the text transparency mask
    color_image = Image.new('RGBA', image.size, fill)
    image.paste(color_image, mask)


def printFinal(img: str):
    # Setup the printer stuff
    p = printer.Usb(0x28e9, 0x0289, out_ep=0x03, profile="ZJ-5870")

    p.image(img)

    # Move the paper a bit so that we have some whitespace to tear it off
    p.control("LF")
    p.control("LF")
    p.control("LF")
    p.control("LF")




# Create a white image
img = Image.new("RGB", (PAPER_WIDTH, 5000), WHITE)

draw = ImageDraw.Draw(img)
font = ImageFont.truetype("Assets/Arial.ttf", active_configuration.font_size)

# Draw two points in top left & right corner to prevent width from being trimmed ;)
draw.point([(0, 0), (PAPER_WIDTH - 1, 0)], BLACK)

txt = "Lorem ipsum dolor sit amet consectetur adipiscing elit."
txt = "The base has fallen. We do not know who the spy is. Proceed with caution. Trust noone. Death to the iron tzar."

#txt = "A short message, oh noes!"

if active_configuration.num_lines > 1:
    parts = SentenceSplitter.findOptimalSplit(txt, active_configuration.num_lines)
else:
    parts = [txt]


# The text size without spacing
total_text_size = len(parts) * active_configuration.font_size
# Now add the spacing (as we only add spacing between lines, we need to use 1 less than the num lines we have (as
# there are 2 spacing between 3 lines and none if we have a single line)
total_text_size += (len(parts) - 1) * active_configuration.line_spacing


if active_configuration.text_alignment == "CENTER":
    # Calculate the location of the top line and count down from there
    text_start_x = PAPER_WIDTH / 2 + total_text_size / 2 + active_configuration.text_offset
    # Draw all the parts

else:
    # Right aligned
    text_start_x = PAPER_WIDTH - (narrow_paper_width / 2 - total_text_size / 2 - active_configuration.text_offset)

    for i, part in enumerate(parts):
        drawRotatedText(img, -90, (text_start_x - i * (active_configuration.font_size + active_configuration.line_spacing), 0), MorseTranslator.textToMorse(part),
                        BLACK, font=font)


# Trim the image so that it's length is correct.
img = trim(img)
text_margin = active_configuration.text_margin
if active_configuration.add_header:
    img = addMargin(img, text_margin, text_margin, text_margin, 0, WHITE)
    img = concatImageVertical(Image.open("Assets/FloralDivider.png"), img)
    img = concatImageVertical(img, Image.open("Assets/FloralDividerUpside.png"))
else:
    img = addMargin(img, text_margin, 0, text_margin, 0, WHITE)

img.save("test.png")

printFinal("test.png")
