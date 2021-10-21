import os
import struct
import pymorton

from os import SEEK_SET
from bmp import write_bmp_file
from helpers import Printer

PAD_HEX = 8
printer = Printer()
printer.on = False
SUPPORTED_PALETTES = [0x100, 0x300, 0x400, 0x900, 0xd00]


class Color:
    r = 0
    g = 0
    b = 0
    a = 0


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
    return num7 * sx + num6


def unscramble_morton(reader, pvr):
    texture_buffer_size = (pvr.width * pvr.height * 2)
    texture_buffer = [0x00] * texture_buffer_size

    for i in range(pvr.width * pvr.height):
        next_index = morton(i, pvr.width, pvr.height)
        channel = struct.unpack("<H", reader.read(2))[0]
        destination_index = int(next_index / 2)
        texture_buffer[destination_index] = channel

    return texture_buffer


def get_color(reader, cur_texture, color_offset):
    palette_offset = 0
    read = Color()

    reader.seek(((cur_texture + 0x800) + color_offset), SEEK_SET)
    palette_offset = struct.unpack("<B", reader.read(1))[0]
    reader.seek(cur_texture + 8 * palette_offset, SEEK_SET)

    read.r = struct.unpack("<H", reader.read(2))[0]
    read.g = struct.unpack("<H", reader.read(2))[0]
    read.b = struct.unpack("<H", reader.read(2))[0]
    read.a = struct.unpack("<H", reader.read(2))[0]

    return read


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


def decompress_scrambled(reader, pvr, cur_texture):
    cur_height = 0
    cur_width = 0
    color_offset = 0
    texture_buffer = [0xFF] * (pvr.width * pvr.height)

    while True:
        cur_width = 0
        if (pvr.width >> 1):
            while True:
                color_offset = pymorton.interleave(cur_height, cur_width)
                color = get_color(reader, cur_texture, color_offset)

                texture_buffer[cur_height * pvr.width * 2 + cur_width * 2] = color.r
                texture_buffer[cur_height * pvr.width * 2 + cur_width * 2 + 1] = color.b
                texture_buffer[pvr.width + cur_height * pvr.width * 2 + cur_width * 2] = color.g
                texture_buffer[pvr.width + cur_height * pvr.width * 2 + cur_width * 2 + 1] = color.a

                cur_width += 1
                if (cur_width >= (pvr.width >> 1)):
                    break
            cur_height += 1
            if (cur_height >= (pvr.height >> 1)):
                break

    return texture_buffer


def decompress_texture(reader, pvr):
    if (pvr.height >> 1 == 0):
        return None

    cur_texture = reader.tell()
    printer("Image data starts at: {}", hex(cur_texture))

    # 2305 and 2306 are special in-sequence palettes (901, 902 in hex)
    # (There's probably a bit that sets these, haven't looked at it)
    if ((pvr.palette & 0xFF00) in [0x900]):
        return decompress_sequenced(reader, pvr)
    elif((pvr.palette & 0xFF00) in [0x100, 0xd00]):
        # Texture is rotated 90 degrees - swap width and height
        pvr.width += pvr.height
        pvr.height = pvr.width - pvr.height
        pvr.width -= pvr.height
        return unscramble_morton(reader, pvr)
    # Scrambled / compressed
    else:
        return decompress_scrambled(reader, pvr, cur_texture)


def export_to_file(ui, filename, decompressed, pvr, texture_off):
    ui.files_extracted += 1
    filename_without_extension = "".join(filename.split(".")[0:-1])

    file_address = int(texture_off + 0x1C)
    out_filename = f"{filename_without_extension}_{file_address:#0{PAD_HEX}x}{ui.files_extracted}.bmp"

    if ui.create_sub_dirs:
        output_dir = os.path.join(ui.output_dir, filename_without_extension)
    else:
        output_dir = ui.output_dir

    output_path = os.path.join(output_dir, out_filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    write_bmp_file(decompressed, pvr.width, pvr.height, output_path, pvr.palette)


def extract_texture(ui, reader, filename, pvr):
    texture_off = reader.tell()

    # skip unsupported textures
    if (pvr.palette & 0xFF00) not in SUPPORTED_PALETTES:
        printer("Not implemented yet: {}.", format(hex(pvr.palette)))
        return False

    decompressed = decompress_texture(reader, pvr)
    export_to_file(ui, filename, decompressed, pvr, texture_off)

    reader.seek(texture_off + pvr.size, SEEK_SET)
