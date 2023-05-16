# Dreamcast PowerVR Format
# See: https://fabiensanglard.net/Mykaruga/tools/segaPVRFormat.txt

import itertools
import struct
from collections import namedtuple
from os import SEEK_SET, SEEK_CUR

import pymorton

PAD_HEX = 8
PRINT_OUTPUT = True
SUPPORTED_FORMATS = [0x100, 0x200, 0x300, 0x400, 0x900, 0xD00]

ColorBlock = namedtuple("ColorBlock", "pixels")


def decode_rectangle(reader, pvr):
    counter = 0
    goal = pvr.width * pvr.height
    texture_buffer = [0xFF] * (pvr.width * pvr.height)

    while counter < goal:
        val_a = struct.unpack("<H", reader.read(2))[0]
        texture_buffer[counter] = val_a
        counter += 1

    return texture_buffer


def morton(index, texture_width, texture_height):
    def most_significant_bit(n):
        return n.bit_length() - 1

    x_bit_position = 1
    y_bit_position = 1
    bit_mask = index
    interleaved_x = 0
    interleaved_y = 0

    msb_width = most_significant_bit(texture_width)
    msb_height = most_significant_bit(texture_height)
    iterations = max(msb_width, msb_height) + 1

    for _ in range(iterations):
        interleaved_x += x_bit_position * (bit_mask & 1)
        bit_mask >>= 1
        x_bit_position *= 2

        interleaved_y += y_bit_position * (bit_mask & 1)
        bit_mask >>= 1
        y_bit_position *= 2

    return int(interleaved_y * texture_width + interleaved_x)


def decode_twiddled(reader, pvr, mipmap=False):
    texture_buffer_size = pvr.width * pvr.height
    texture_buffer = [0x00] * texture_buffer_size

    if mipmap:
        mip_level_start_index = calculate_mip_level_start_index(pvr.width) * 2
        reader.seek(reader.tell() + mip_level_start_index, SEEK_SET)

    chunk_size = min(pvr.width, pvr.height)
    chunks_wide = pvr.width // chunk_size
    chunks_high = pvr.height // chunk_size
    total_chunks = max(chunks_wide, chunks_high)

    for chunk_index in range(total_chunks):
        chunk_x = chunk_index % chunks_wide
        chunk_y = chunk_index // chunks_wide
        chunk_offset_x = chunk_x * chunk_size
        chunk_offset_y = chunk_y * chunk_size

        for i in range(chunk_size * chunk_size):
            destination_index = morton(i, chunk_size, chunk_size)
            x, y = destination_index % chunk_size, destination_index // chunk_size

            new_x, new_y = chunk_size - y - 1, x
            new_x = chunk_size - new_x - 1

            new_x += chunk_offset_x
            new_y += chunk_offset_y

            updated_destination_index = new_y * pvr.width + new_x
            channel = struct.unpack("<H", reader.read(2))[0]
            texture_buffer[updated_destination_index] = channel

    return texture_buffer


def calculate_mip_level_start_index(mip_level_dimension):
    start_index = 1
    while mip_level_dimension:
        mip_level_dimension >>= 1
        start_index += mip_level_dimension * mip_level_dimension
    return start_index


def get_color_block(reader, texture_offset, color_offset):
    reader.seek(texture_offset + 0x800 + color_offset)
    palette_offset = struct.unpack("<B", reader.read(1))[0]

    reader.seek(texture_offset + 8 * palette_offset)
    pixels = [struct.unpack("<H", reader.read(2))[0] for _ in range(4)]
    return ColorBlock(pixels)


def decode_twiddled_vq(reader, pvr, texture_offset, mipmap=False):
    texture_buffer = [0xFF] * (pvr.width * pvr.height)
    width_times_two = pvr.width * 2

    mip_level_offset = calculate_mip_level_start_index(pvr.width // 2) if mipmap else 0

    for row, col in itertools.product(range(pvr.height // 2), range(pvr.width // 2)):
        color_offset = pymorton.interleave(row, col) + mip_level_offset
        color_block = get_color_block(reader, texture_offset, color_offset)

        base_index = row * width_times_two + col * 2
        texture_buffer[base_index] = color_block.pixels[0]
        texture_buffer[base_index + 1] = color_block.pixels[2]
        texture_buffer[base_index + pvr.width] = color_block.pixels[1]
        texture_buffer[base_index + pvr.width + 1] = color_block.pixels[3]

    return texture_buffer


def skip_unsupported(pvr, output_strings, texture_type):
    if (pvr.pixel_format & 0xFF00) not in SUPPORTED_FORMATS:
        if PRINT_OUTPUT:
            output_strings.append(f"Not implemented yet: {hex(pvr.pixel_format)} - {texture_type}.")
        return None


def decompress_texture(reader, pvr, output_strings):
    if pvr.height >> 1 == 0:
        return None

    decoding_functions = {
        0x000: lambda: skip_unsupported(pvr, output_strings, "UNKNOWN"),  # Unknown
        0x100: lambda: decode_twiddled(reader, pvr),  # Square twiddled
        0x200: lambda: decode_twiddled(reader, pvr, True),  # Square twiddled & mipmap (Unimplemented)
        0x300: lambda: decode_twiddled_vq(reader, pvr, reader.tell()),  # VQ
        0x400: lambda: decode_twiddled_vq(reader, pvr, reader.tell(), True),  # VQ & mipmap
        0x500: lambda: skip_unsupported(pvr, output_strings, "8-BIT CLUT TWIDDLED"),  # 8-bit CLUT twiddled
        0x600: lambda: skip_unsupported(pvr, output_strings, "4-BIT CLUT TWIDDLED"),  # 4-bit CLUT twiddled
        0x700: lambda: skip_unsupported(pvr, output_strings, "8-BIT DIRECT TWIDDLED"),  # 8-bit direct twiddled
        0x800: lambda: skip_unsupported(pvr, output_strings, "4-BIT DIRECT TWIDDLED"),  # 4-bit direct twiddled
        0x900: lambda: decode_rectangle(reader, pvr),  # Rectangle
        0xA00: lambda: skip_unsupported(pvr, output_strings, "UNKNOWN"),  # Unknown
        0xB00: lambda: skip_unsupported(pvr, output_strings, "RECTANGULAR STRIDE"),  # Rectanglular stride
        0xC00: lambda: skip_unsupported(pvr, output_strings, "UNKNOWN"),  # Unknown
        0xD00: lambda: decode_twiddled(reader, pvr),  # Rectanglular twiddled
        0xE00: lambda: skip_unsupported(pvr, output_strings, "UNKNOWN"),  # Unknown
        0xF00: lambda: skip_unsupported(pvr, output_strings, "UNKNOWN"),  # Unknown
        0x1000: lambda: skip_unsupported(pvr, output_strings, "SMALL VQ"),  # Small VQ
        0x1100: lambda: skip_unsupported(pvr, output_strings, "SMALL VQ & MIPMAP"),  # Small VQ & mipmap
        0x1200: lambda: skip_unsupported(pvr, output_strings, "SQUARE TWIDDLED & MIPMAP"),  # Square twiddled & mipmap
    }

    palette_type = pvr.pixel_format & 0xFF00
    decode_function = decoding_functions.get(palette_type)
    return decode_function()


def extract_16bit_texture(reader, pvr, output_strings):
    decompressed = decompress_texture(reader, pvr, output_strings)
    reader.seek(pvr.texture_offset + pvr.size, SEEK_SET)
    return decompressed
