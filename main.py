
from escpos import printer

from PIL import Image, ImageDraw, ImageChops, ImageFont, ImageOps

from SentenceSplitter import SentenceSplitter

PAPER_WIDTH = 384

FONT_SIZE = 50
LINE_SPACING = 20
TEXT_MARGIN = 20
TEXT_OFFSET = 10  # Since we use dots, it makes the text seem not centered otherwise.

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

MORSE_CODE_DICT = { 'A': '.-', 'B': '-...',
                    'C': '-.-.', 'D': '-..', 'E': '.',
                    'F': '..-.', 'G': '--.', 'H': '....',
                    'I': '..', 'J': '.---', 'K': '-.-',
                    'L': '.-..', 'M': '--', 'N': '-.',
                    'O': '---', 'P': '.--.', 'Q': '--.-',
                    'R': '.-.', 'S': '...', 'T': '-',
                    'U': '..-', 'V': '...-', 'W': '.--',
                    'X': '-..-', 'Y': '-.--', 'Z': '--..',
                    '1': '.----', '2': '..---', '3': '...--',
                    '4': '....-', '5': '.....', '6': '-....',
                    '7': '--...', '8': '---..', '9': '----.',
                    '0': '-----', ', ': '--..--', '.': '.-.-.-',
                    '?': '..--..', '/': '-..-.', '-': '-....-',
                    '(': '-.--.', ')': '-.--.-', '!': '-.-.--'}


def textToMorse(message):
    cipher = ""

    for letter in message:
        if letter != ' ':
            cipher += MORSE_CODE_DICT[letter.upper()] + ' '
        else:
            cipher += ' '
    return cipher


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


# Create a white image
img = Image.new("RGB", (PAPER_WIDTH, 5000), WHITE)

draw = ImageDraw.Draw(img)
font = ImageFont.truetype("Arial.ttf", FONT_SIZE)

# Draw two points in top left & right corner to prevent width from being trimmed ;)
draw.point([(0, 0), (PAPER_WIDTH - 1, 0)], BLACK)

txt = "Lorem ipsum dolor sit amet consectetur adipiscing elit. Aenean ac mi sit amet nulla convallis aliquet."
txt = "This is a very short message"

parts = SentenceSplitter.findOptimalSplit(txt, 6)

# Calculate the location of the top line and count down from there
font_center_x = PAPER_WIDTH / 2 + len(parts) * FONT_SIZE / 2 + (len(parts) - 1) * LINE_SPACING * 0.5 + TEXT_OFFSET

# Draw all the parts
for i, part in enumerate(parts):
    drawRotatedText(img, -90, (font_center_x - i * (FONT_SIZE + LINE_SPACING), 0), textToMorse(part), BLACK, font=font)


# Trim the image so that it's length is correct.
img = trim(img)
img = addMargin(img, TEXT_MARGIN, TEXT_MARGIN, TEXT_MARGIN, 0, WHITE)

img = concatImageVertical(Image.open("FloralDivider.png"), img)
img = concatImageVertical(img, Image.open("FloralDividerUpside.png"))
img.save("test.png")

# Setup the printer stuff
p = printer.Usb(0x28e9, 0x0289, out_ep= 0x03, profile = "ZJ-5870")
p.image("test.png")

# Move the paper a bit so that we have some whitespace to tear it off
p.control("LF")
p.control("LF")
p.control("LF")
p.control("LF")