import os
import struct
import traceback

from os import SEEK_SET
from bmp import write_bmp_file
from moser import bruijn
from PyQt5.QtWidgets import (QTableWidgetItem)
from helpers import Printer

PAD_HEX = 8
printer = Printer()
printer.on = False
print_traceback = False


class Mem:
    unk = [0]
    add1 = [0] * 3  # v19
    buffer = 0
    add2 = [0] * 2


class PSXPVR:
    unk = [0] * 16
    width = 0
    height = 0
    palette = 0
    size = 0


class Color:
    r = 0
    g = 0
    b = 0
    a = 0


def get_add1(reader):
    # loc_4C9BAF
    reader.seek(4)

    add1 = struct.unpack("<I", reader.read(4))[0]

    if add1 == 0xFFFFFFFF:
        return True

    # loc_4C9BBF
    new_add = add1
    while new_add != 0xFFFFFFFF:
        reader.seek(add1 + 4, SEEK_SET)
        new_add = struct.unpack("<I", reader.read(4))[0]

        add1 += new_add + 8

        reader.seek(add1, SEEK_SET)
        new_add = struct.unpack("<I", reader.read(4))[0]

    add1 += 4
    return add1


def get_v13(reader):
    reader.seek(8, SEEK_SET)
    v13 = struct.unpack("<I", reader.read(4))[0]
    reader.seek((9 * v13 + 3) * 4, SEEK_SET)
    return v13


def get_v101(reader, mem, v13):
    reader.seek((v13 * 4) + mem.add1[0], SEEK_SET)
    return struct.unpack("<I", reader.read(4))[0]


def get_v35(v13, v101, v34):
    return v34 + ((v13 + v101) * 4 + 8)


def get_num_textures(reader, v41):
    reader.seek(v41, SEEK_SET)
    return struct.unpack("<I", reader.read(4))[0]


def get_textures_add(reader, num_textures):
    tmp = 0
    for i in range(num_textures):
        tmp = struct.unpack("<I", reader.read(4))[0]
        print("{}: {}\n", i + 1, hex(tmp))


def get_v31(reader, cur_texture, v30):
    color_offset = 0
    reader.seek(((cur_texture + 0x800) + v30), SEEK_SET)
    color_offset = struct.unpack("<B", reader.read(1))[0]

    read = Color()
    reader.seek(cur_texture + 8 * color_offset, SEEK_SET)
    read.r = struct.unpack("<H", reader.read(2))[0]
    read.g = struct.unpack("<H", reader.read(2))[0]
    read.b = struct.unpack("<H", reader.read(2))[0]
    read.a = struct.unpack("<H", reader.read(2))[0]

    return read


def decompress_texture(reader, pvr):
    actual_width = pvr.width >> 1
    actual_height = pvr.height >> 1
    if (actual_width >= actual_height):
        actual_width = pvr.height >> 1

    v20 = actual_width - 1
    v32 = 0
    if (v20 & 1):
        i = 1
        while i & v20:
            i *= 2
            v32 += 1

    texture_buffer = [0xFF] * (pvr.width * pvr.height)
    cur_texture = reader.tell()

    if (actual_height == 0):
        return None

    # 2305 and 2306 are special in-sequence palettes (901, 902 in hex)
    # (There's probably a bit that sets these, haven't looked at it)
    # Adding the unsupported ones to see if they work as-is
    # in_sequence_palettes = [64, 65, 66, 1025, 2305, 2306, 3329]
    in_sequence = (pvr.palette == 2305) or (pvr.palette == 2306)

    if (in_sequence):
        counter = 0
        goal = (pvr.width * pvr.height)

        while True:
            val_a = struct.unpack("<H", reader.read(2))[0]
            texture_buffer[counter] = val_a
            counter += 1
            if (counter >= goal):
                break

    # Scrambled / compressed
    else:
        cur_height = 0
        cur_width = 0
        v30 = 0

        while True:
            cur_width = 0
            if (pvr.width >> 1):
                while True:
                    v30 = bruijn[v20 & cur_height] | 2 * bruijn[v20 & cur_width] | ((~v20 & (cur_height | cur_width)) << v32)
                    v31 = get_v31(reader, cur_texture, v30)

                    texture_buffer[cur_height * pvr.width * 2 + cur_width * 2] = v31.r
                    texture_buffer[cur_height * pvr.width * 2 + cur_width * 2 + 1] = v31.b
                    texture_buffer[pvr.width + cur_height * pvr.width * 2 + cur_width * 2] = v31.g
                    texture_buffer[pvr.width + cur_height * pvr.width * 2 + cur_width * 2 + 1] = v31.a

                    cur_width += 1
                    if (cur_width >= (pvr.width >> 1)):
                        break
                cur_height += 1
                if (cur_height >= (pvr.height >> 1)):
                    break

    return texture_buffer


def extract_texture(ui, reader, filename):
    texture_off = struct.unpack("<I", reader.read(4))[0]

    # save current offset
    current_off = reader.tell()

    pvr = PSXPVR()
    reader.seek(texture_off, SEEK_SET)

    for i in range(16):
        pvr.unk[i] = struct.unpack("<B", reader.read(1))[0]
    pvr.width = struct.unpack("<H", reader.read(2))[0]
    pvr.height = struct.unpack("<H", reader.read(2))[0]
    pvr.palette = struct.unpack("<I", reader.read(4))[0]
    pvr.size = struct.unpack("<I", reader.read(4))[0]

    # skip unsupported textures
    # if (pvr.palette & 0xFF00) != 0x300:
    #     printer("Not implemented yet: {}.", format(hex(pvr.palette)))
    #     return False

    decompressed = decompress_texture(reader, pvr)
    export_to_file(ui, filename, decompressed, pvr, texture_off)

    reader.seek(current_off, SEEK_SET)
    return True


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


def extract_textures(ui, filename, directory, file_index):
    input_file = os.path.join(directory, filename)
    mem = Mem()
    v13 = 0
    v35 = 0
    v37 = 0
    v41 = 0
    v101 = 0
    num_textures = 0
    textures_written = 0

    with open(input_file, "rb") as input:
        mem.add1[0] = get_add1(input)
        v13 = get_v13(input)
        v101 = get_v101(input, mem, v13)
        v35 = get_v35(v13, v101, mem.add1[0] - 4)

        v37 = v35 + 4
        v41 = v37 + 4

        num_textures = get_num_textures(input, v41)
        ui.fileTable.setItem(file_index, 1, QTableWidgetItem(str(num_textures)))

        printer("ADD1: {1:0{0}X} {2:0{0}X} {3:0{0}X}", PAD_HEX, mem.add1[0], mem.add1[1], mem.add1[2])
        printer("v13:  {1:0{0}X} v101: {2:0{0}X} v35: {3:0{0}X}\nv41:  {4:0{0}X}", PAD_HEX, v13, v101, v35, v41)
        printer("There are {} textures.\n", num_textures)

        for _ in range(num_textures):
            try:
                if extract_texture(ui, input, filename):
                    textures_written += 1
            except Exception as e:
                printer("Tried proceesing an unsupported texture in {}. The error was: {}", filename, e)
                if print_traceback:
                    traceback.print_exc()

        if num_textures > 0:
            ui.fileTable.setItem(file_index, 2, QTableWidgetItem(str(textures_written)))
            if num_textures == textures_written:
                ui.fileTable.setItem(file_index, 3, QTableWidgetItem("OK"))
            else:
                ui.fileTable.setItem(file_index, 3, QTableWidgetItem("ERROR"))
        else:
            ui.fileTable.setItem(file_index, 3, QTableWidgetItem("SKIPPED"))
        input.close()
