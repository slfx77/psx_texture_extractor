import struct
import pymorton

from os import SEEK_SET
from helpers import Printer
from color_helpers import get_16bpp_color_params, convert_16bpp_to_32bpp

PAD_HEX = 8
printer = Printer()
printer.on = False
SUPPORTED_PALETTES = [0x100, 0x300, 0x400, 0x900, 0xd00]


class Color:
    block = [None] * 4


# Borrowed from Rawtex
def morton(t, sx, sy):
    num1 = 1
    num2 = 1
    num3 = t
    num4 = sx
    num5 = sy
    num6 = 0
    num7 = 0
    while (num4 > 1 or num5 > 1):
        if (num4 > 1):
            num6 += num2 * (num3 & 1)
            num3 >>= 1
            num2 *= 2
            num4 >>= 1
        if (num5 > 1):
            num7 += num1 * (num3 & 1)
            num3 >>= 1
            num1 *= 2
            num5 >>= 1
    return int(num7 * sx + num6)


def get_color(reader, cur_texture, color_offset):
    palette_offset = 0
    color = Color()

    reader.seek(((cur_texture + 0x800) + color_offset), SEEK_SET)
    palette_offset = struct.unpack("<B", reader.read(1))[0]
    reader.seek(cur_texture + 8 * palette_offset, SEEK_SET)

    color.block[0] = struct.unpack("<H", reader.read(2))[0]
    color.block[1] = struct.unpack("<H", reader.read(2))[0]
    color.block[2] = struct.unpack("<H", reader.read(2))[0]
    color.block[3] = struct.unpack("<H", reader.read(2))[0]

    return color


def decompress_sequenced(reader, pvr):
    counter = 0
    goal = (pvr.width * pvr.height)
    texture_buffer = [0xFF] * (pvr.width * pvr.height)

    while True:
        val_a = struct.unpack("<H", reader.read(2))[0]
        texture_buffer[counter] = val_a
        counter += 1
        if (counter >= goal):
            break

    return texture_buffer


def decompress_morton(reader, pvr):
    texture_buffer_size = pvr.width * pvr.height
    # Read texture data and store it in a list called texture_buffer
    texture_buffer = [struct.unpack("<H", reader.read(2))[0] for _ in range(texture_buffer_size)]

    # Rearrange the texture data based on the Morton order
    # by creating a new list where each element is taken from the original texture_buffer list
    # using the calculated destination_index (Morton order)
    return [texture_buffer[morton(i, pvr.width, pvr.height)] for i in range(texture_buffer_size)]

def decompress_scrambled(reader, pvr, cur_texture):
    # Initialize the texture_buffer with the size of the final texture
    texture_buffer = [0xFF] * (pvr.width * pvr.height)

    # Loop through each block of 2x2 pixels in the texture (width and height are divided by 2)
    for cur_height in range(pvr.height >> 1):
        for cur_width in range(pvr.width >> 1):
            # Calculate the color_offset using Morton order encoding
            color_offset = pymorton.interleave(cur_height, cur_width)
            # Get the color data for the current block
            color = get_color(reader, cur_texture, color_offset)

            # Fill the texture_buffer with the color data
            texture_buffer[cur_height * pvr.width * 2 + cur_width * 2] = color.block[0]
            texture_buffer[cur_height * pvr.width * 2 + cur_width * 2 + 1] = color.block[2]
            texture_buffer[pvr.width + cur_height * pvr.width * 2 + cur_width * 2] = color.block[1]
            texture_buffer[pvr.width + cur_height * pvr.width * 2 + cur_width * 2 + 1] = color.block[3]

    # Return the texture_buffer with the decompressed texture data
    return texture_buffer

def decompress_texture(reader, pvr):
    if (pvr.height >> 1 == 0):
        return None

    cur_texture = reader.tell()
    printer("Image data starts at: {}", hex(cur_texture))

    # 901 and 902 are special in-sequence palettes
    if ((pvr.palette & 0xFF00) in [0x900]):
        return decompress_sequenced(reader, pvr)
    elif((pvr.palette & 0xFF00) in [0x100, 0xd00]):
        # Texture is stored rotated 90 degrees - swap width and height
        pvr.width += pvr.height
        pvr.height = pvr.width - pvr.height
        pvr.width -= pvr.height
        return decompress_morton(reader, pvr)
    # Scrambled / compressed
    else:
        return decompress_scrambled(reader, pvr, cur_texture)


def convert_texture_for_pypng(texture, pvr):
    params = get_16bpp_color_params(pvr.palette)

    pixels = []
    pixel_row = []

    for i in texture:
        pixel_row += convert_16bpp_to_32bpp(params, i)
        if(len(pixel_row) == pvr.width * 4):
            pixels.append(pixel_row)
            pixel_row = []

    return pixels


def extract_16bit_texture(reader, pvr):
    # skip unsupported textures
    if (pvr.palette & 0xFF00) not in SUPPORTED_PALETTES:
        printer("Not implemented yet: {}.", format(hex(pvr.palette)))
        return False

    decompressed = decompress_texture(reader, pvr)

    reader.seek(pvr.texture_offset + pvr.size, SEEK_SET)
    return convert_texture_for_pypng(decompressed, pvr)
