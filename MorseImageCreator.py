from PIL import Image, ImageDraw, ImageChops, ImageFont, ImageOps

from Config import Config
from MorseTranslator import MorseTranslator
from SentenceSplitter import SentenceSplitter


class MorseImageCreator:
    PAPER_WIDTH = 384
    wide_paper_width = 384
    narrow_paper_width = 194

    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)

    @staticmethod
    def trim(image: Image) -> Image:
        inverted_image = image.convert("RGB")
        inverted_image = ImageOps.invert(inverted_image)
        return image.crop(inverted_image.getbbox())

    @staticmethod
    def addMargin(image: Image, top: int, right: int, bottom: int, left: int, color) -> Image:
        width, height = image.size
        new_width = width + right + left
        new_height = height + top + bottom
        result = Image.new(image.mode, (new_width, new_height), color)
        result.paste(image, (left, top))
        return result

    @staticmethod
    def concatImageVertical(image_1: Image, image_2: Image) -> Image:
        dst = Image.new('RGB', (image_1.width, image_1.height + image_2.height))
        dst.paste(image_1, (0, 0))
        dst.paste(image_2, (0, image_1.height))
        return dst

    @staticmethod
    def drawRotatedText(image: Image, angle: float, xy, text, fill_color, *args, **kwargs):
        """ Draw text at an angle into an image, takes the same arguments
            as Image.text() except for:

        :param image: Image to write text into (note that this image is modified in place)
        :param angle: Angle to write text at
        :param xy: The XY location of the text
        :param text: The text to write
        :param fill_color: The color to fill with after the rotate
        """
        # Get the size of our image
        width, height = image.size
        max_dim = max(width, height)

        # Build a transparency mask large enough to hold the text
        mask_size = (max_dim * 2, max_dim * 2)
        mask = Image.new('L', mask_size, 0)

        # Add text to mask
        draw = ImageDraw.Draw(mask)
        draw.text((max_dim, max_dim), text, 255, *args, **kwargs)

        if angle % 90 == 0:
            # Rotate by multiple of 90 deg is easier
            rotated_mask = mask.rotate(angle)
        else:
            # Rotate an an enlarged mask to minimize jaggies
            bigger_mask = mask.resize((max_dim * 8, max_dim * 8), resample=Image.BICUBIC)
            rotated_mask = bigger_mask.rotate(angle).resize(mask_size, resample=Image.LANCZOS)

        # Crop the mask to match image
        mask_xy = (max_dim - xy[0], max_dim - xy[1])
        b_box = mask_xy + (mask_xy[0] + width, mask_xy[1] + height)
        mask = rotated_mask.crop(b_box)

        # Paste the appropriate color, with the text transparency mask
        color_image = Image.new('RGBA', image.size, fill_color)
        image.paste(color_image, mask)

    @staticmethod
    def createImage(text: str, config: Config) -> Image:
        # Create a white image
        img = Image.new("RGB", (MorseImageCreator.PAPER_WIDTH, 5000), MorseImageCreator.WHITE)

        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("Assets/Arial.ttf", config.font_size)

        # Draw two points in top left & right corner to prevent width from being trimmed ;)
        draw.point([(0, 0), (MorseImageCreator.PAPER_WIDTH - 1, 0)], MorseImageCreator.BLACK)

        if config.num_lines > 1:
            parts = SentenceSplitter.findOptimalSplit(text, config.num_lines)
        else:
            parts = [text]

        # The text size without spacing
        total_text_size = len(parts) * config.font_size
        # Now add the spacing (as we only add spacing between lines, we need to use 1 less than the num lines we have
        # (as there are 2 spacing between 3 lines and none if we have a single line)
        total_text_size += (len(parts) - 1) * config.line_spacing

        if config.text_alignment == "CENTER":
            # Calculate the location of the top line and count down from there
            text_start_x = MorseImageCreator.PAPER_WIDTH / 2 + total_text_size / 2 + config.text_offset
            # Draw all the parts

        else:
            # Right aligned
            text_start_x = MorseImageCreator.PAPER_WIDTH - (
                    MorseImageCreator.narrow_paper_width / 2 - total_text_size / 2 - config.text_offset)

            for i, part in enumerate(parts):
                MorseImageCreator.drawRotatedText(img, -90,
                                                  (text_start_x - i * (config.font_size + config.line_spacing), 0),
                                                  MorseTranslator.textToMorse(part),
                                                  MorseImageCreator.BLACK, font=font)

        # Trim the image so that it's length is correct.
        img = MorseImageCreator.trim(img)
        text_margin = config.text_margin
        if config.add_header:
            img = MorseImageCreator.addMargin(img, text_margin, text_margin, text_margin, 0, MorseImageCreator.WHITE)
            img = MorseImageCreator.concatImageVertical(Image.open("Assets/FloralDivider.png"), img)
            img = MorseImageCreator.concatImageVertical(img, Image.open("Assets/FloralDividerUpside.png"))
        else:
            img = MorseImageCreator.addMargin(img, text_margin, 0, text_margin, 0, MorseImageCreator.WHITE)
        return img
