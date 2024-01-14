class Config:
    def __init__(self, text_alignment: str, font_size: int, line_spacing: int, text_margin: int, text_offset: int,
                 num_lines: int, add_headers: bool):
        self.text_alignment: str = text_alignment

        self.font_size: int = font_size
        self.line_spacing: int = line_spacing
        self.text_margin: int = text_margin
        self.text_offset: int = text_offset  # Since we use dots, it makes the text seem not centered otherwise.
        self.num_lines: int = num_lines
        self.add_header: bool = add_headers
