import struct
import numpy as np


class BmpFileHeader:
    type = 0
    size = 0
    reserved1 = 0
    reserved2 = 0
    off_bits = 0


class BmpImageHeader:
    header_size = 0
    width = 0
    height = 0
    planes = 0
    bit_count = 0
    compression = 0
    size_of_image = 0
    xpm = 0
    ypm = 0
    clr_used = 0
    clr_imp = 0
    red_mask = 0
    green_mask = 0
    blue_mask = 0
    alpha_mask = 0
    cs_type = 0
    cie = [0] * 9
    gamma = [0] * 3


class Bmp:
    file = BmpFileHeader()
    image = BmpImageHeader()


def write_bmp_file(buffer, width, height, file_name, palette):
    extracted = Bmp()

    # Setup File Header
    extracted.file.type = np.frombuffer(b'BM', dtype='<H')[0]
    extracted.file.size = 122 + width * height * 2
    extracted.file.off_bits = 122

    # Image Header
    extracted.image.header_size = 108
    extracted.image.width = width
    extracted.image.height = -height
    extracted.image.planes = 1
    extracted.image.bit_count = 16
    extracted.image.compression = 3  # BI_BITFIELDS
    extracted.image.size_of_image = width * height * 2
    extracted.image.xpm = extracted.image.ypm = extracted.image.clr_used = extracted.image.clr_imp = 0

    # Default / 769
    red_mask = 0xF800
    green_mask = 0x7E0
    blue_mask = 0x1F
    alpha_mask = 0

    # 4444

    if palette == 770 or palette == 2306:
        extracted.image.red_mask = 0x0F00
        extracted.image.green_mask = 0xF0
        extracted.image.blue_mask = 0xF
        extracted.image.alpha_mask = 0xF000

    # 5551
    # Alpha is either 0 or 128 for some reason

    elif palette == 768:
        extracted.image.red_mask = 0x7C00
        extracted.image.green_mask = 0x3E0
        extracted.image.blue_mask = 0x1F
        extracted.image.alpha_mask = 0x8000

    # 565
    # Pixels are not scrambled!

    elif palette == 2305:
        extracted.image.red_mask = 0xF800
        extracted.image.green_mask = 0x7E0
        extracted.image.blue_mask = 0x1F
        extracted.image.alpha_mask = 0

    # OTHER

    else:
        extracted.image.red_mask = red_mask
        extracted.image.green_mask = green_mask
        extracted.image.blue_mask = blue_mask
        extracted.image.alpha_mask = alpha_mask

    with open(file_name, "wb") as output:
        output.write(struct.pack("<H", extracted.file.type))
        output.write(struct.pack("<I", extracted.file.size))
        output.write(struct.pack("<H", extracted.file.reserved1))
        output.write(struct.pack("<H", extracted.file.reserved2))
        output.write(struct.pack("<I", extracted.file.off_bits))
        output.write(struct.pack("<I", extracted.image.header_size))
        output.write(struct.pack("<I", extracted.image.width))
        output.write(struct.pack("<i", extracted.image.height))
        output.write(struct.pack("<H", extracted.image.planes))
        output.write(struct.pack("<H", extracted.image.bit_count))
        output.write(struct.pack("<I", extracted.image.compression))
        output.write(struct.pack("<I", extracted.image.size_of_image))
        output.write(struct.pack("<I", extracted.image.xpm))
        output.write(struct.pack("<I", extracted.image.ypm))
        output.write(struct.pack("<I", extracted.image.clr_used))
        output.write(struct.pack("<I", extracted.image.clr_imp))
        output.write(struct.pack("<I", extracted.image.red_mask))
        output.write(struct.pack("<I", extracted.image.green_mask))
        output.write(struct.pack("<I", extracted.image.blue_mask))
        output.write(struct.pack("<I", extracted.image.alpha_mask))
        output.write(struct.pack("<I", extracted.image.cs_type))
        for i in range(3 * 3):
            output.write(struct.pack("<I", extracted.image.cie[i]))
        for i in range(3):
            output.write(struct.pack("<I", extracted.image.gamma[i]))
        for i in buffer:
            output.write(struct.pack("<H", i))
        output.close()
