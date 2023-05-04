import itertools
import struct
from collections import namedtuple
from os import SEEK_SET

import pymorton

from color_helpers import convert_16bpp_to_32bpp, get_16bpp_color_params

PAD_HEX = 8
print_output = False
SUPPORTED_PALETTES = [0x100, 0x300, 0x400, 0x900, 0xD00]


ColorBlock = namedtuple("ColorBlock", "pixels")


# Borrowed from Rawtex
def morton(index, texture_width, texture_height):
    x_bit_position = 1
    y_bit_position = 1
    bit_mask = index
    x_dimension = texture_width
    y_dimension = texture_height
    interleaved_x = 0
    interleaved_y = 0

    while x_dimension > 1 or y_dimension > 1:
        if x_dimension > 1:
            interleaved_x += x_bit_position * (bit_mask & 1)
            bit_mask >>= 1
            x_bit_position *= 2
            x_dimension >>= 1
        if y_dimension > 1:
            interleaved_y += y_bit_position * (bit_mask & 1)
            bit_mask >>= 1
            y_bit_position *= 2
            y_dimension >>= 1

    return int(interleaved_y * texture_width + interleaved_x)


def get_color_block(reader, cur_texture, color_offset):
    palette_offset = 0

    reader.seek(((cur_texture + 0x800) + color_offset), SEEK_SET)
    palette_offset = struct.unpack("<B", reader.read(1))[0]
    reader.seek(cur_texture + 8 * palette_offset, SEEK_SET)

    pixels = [struct.unpack("<H", reader.read(2))[0] for _ in range(4)]
    return ColorBlock(pixels)


def decompress_sequenced(reader, pvr):
    counter = 0
    goal = pvr.width * pvr.height
    texture_buffer = [0xFF] * (pvr.width * pvr.height)

    while True:
        val_a = struct.unpack("<H", reader.read(2))[0]
        texture_buffer[counter] = val_a
        counter += 1
        if counter >= goal:
            break

    return texture_buffer


def decompress_morton(reader, pvr):
    texture_buffer_size = pvr.width * pvr.height
    texture_buffer = [0x00] * texture_buffer_size

    chunk_size = min(pvr.width, pvr.height)
    chunks_wide = pvr.width // chunk_size
    chunks_high = pvr.height // chunk_size

    for chunk_y in range(chunks_high):
        for chunk_x in range(chunks_wide):
            for i in range(chunk_size * chunk_size):
                destination_index = morton(i, chunk_size, chunk_size)
                x, y = destination_index % chunk_size, destination_index // chunk_size

                # Rotate 90 degrees counter-clockwise
                new_x, new_y = chunk_size - y - 1, x

                # Mirror horizontally
                new_x = chunk_size - new_x - 1

                # Offset for chunk position
                new_x += chunk_x * chunk_size
                new_y += chunk_y * chunk_size

                updated_destination_index = new_y * pvr.width + new_x
                channel = struct.unpack("<H", reader.read(2))[0]
                texture_buffer[updated_destination_index] = channel

    return texture_buffer


def decompress_scrambled(reader, pvr, cur_texture):
    # Initialize the texture_buffer with the size of the final texture
    texture_buffer = [0xFF] * (pvr.width * pvr.height)

    width_times_two = pvr.width * 2

    # Loop through each block of 2x2 pixels in the texture
    for row, col in itertools.product(range(pvr.height // 2), range(pvr.width // 2)):
        # Calculate the color_offset using Morton order encoding
        color_offset = pymorton.interleave(row, col)
        # Get the color data for the current block
        color_block = get_color_block(reader, cur_texture, color_offset)

        # Fill the texture_buffer with the color data
        base_index = row * width_times_two + col * 2
        texture_buffer[base_index] = color_block.pixels[0]
        texture_buffer[base_index + 1] = color_block.pixels[2]
        texture_buffer[base_index + pvr.width] = color_block.pixels[1]
        texture_buffer[base_index + pvr.width + 1] = color_block.pixels[3]

    # Return the texture_buffer with the decompressed texture data
    return texture_buffer


def decompress_texture(reader, pvr, output_strings):
    if pvr.height >> 1 == 0:
        return None

    cur_texture = reader.tell()
    if print_output:
        output_strings.append(f"Image data starts at: {hex(cur_texture)}")

    # 901 and 902 are special in-sequence palettes
    if (pvr.palette & 0xFF00) in [0x900]:
        return decompress_sequenced(reader, pvr)
    elif (pvr.palette & 0xFF00) in [0x100, 0xD00]:
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
        if len(pixel_row) == pvr.width * 4:
            pixels.append(pixel_row)
            pixel_row = []

    return pixels


def extract_16bit_texture(reader, pvr, output_strings):
    # skip unsupported textures
    if (pvr.palette & 0xFF00) not in SUPPORTED_PALETTES:
        if print_output:
            output_strings.append(f"Not implemented yet: {hex(pvr.palette)}.")
        return False

    decompressed = decompress_texture(reader, pvr, output_strings)

    reader.seek(pvr.texture_offset + pvr.size, SEEK_SET)
    return convert_texture_for_pypng(decompressed, pvr)
