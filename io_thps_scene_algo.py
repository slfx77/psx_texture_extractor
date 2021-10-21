import os
import struct


from PyQt5.QtWidgets import (QTableWidgetItem)
from psx_pvr import PSXPVR
from helpers import Printer, fix_and_write_to_png
from extract_psx_algo import extract_texture
from math import log2

printer = Printer()
printer.on = False
fancy_output = True


def print_current_position(reader):
    printer("I am at: {}", hex(reader.tell()))


def ps1_to_32bpp(color):
    r = (color) & 0x1F
    g = (color >> 5) & 0x1F
    b = (color >> 10) & 0x1F
    a = (color >> 15) & 0x1

    if r == 31 and g == 0 and b == 31:
        # Fully transparent
        return [0, 0, 0, 0]
    else:
        return [int((r/32)*255), int((g/32)*255), int((b/32)*255), 255]


def skip_model_data(reader):
    ptr_meta, obj_count, = struct.unpack("<II", reader.read(8))
    printer("Num objects: {}", obj_count)

    # "Objects" are 36 bytes. Skip over them for reading textures.
    for _ in range(obj_count):
        # Skip over object data
        reader.read(36)

    # Determine number of meshes (we need to skip over the mesh name list before texture info)
    mesh_count = struct.unpack("<I", reader.read(4))[0]
    printer("Num meshes: {}", mesh_count)

    # Skip to the tagged chunks, find the textures
    reader.seek(ptr_meta)
    chunk_count = -1
    while True:
        magic = reader.read(4)
        chunk_count += 1
        if magic != b"\xFF\xFF\xFF\xFF":
            printer("SKIPPED CHUNK: 0x{}", magic.hex())
            unk_length = struct.unpack("<I", reader.read(4))[0]
            reader.read(unk_length)
            if chunk_count > 16:
                # There should not be this many tagged chunks, must be a file error
                raise Exception("Unable to parse PSX texture library, cannot find texture data")
        else:
            printer("{}", "END OF TAGGED CHUNKS")
            break

    # Now we are at the model names list - if there are any models
    for _ in range(mesh_count):
        reader.read(4)


def read_texture_info(reader):
    # Print position where texture data starts
    print_current_position(reader)

    # Read number of textures
    num_tex = struct.unpack("<I", reader.read(4))[0]
    printer("Num textures: {}", num_tex)

    tex_names = []
    for _ in range(num_tex):
        tex_names.append(struct.unpack("<I", reader.read(4))[0])
    return tex_names


def read_4bit_palettes(reader):
    # Read 16-color palettes
    num_4bit = struct.unpack("<I", reader.read(4))[0]
    printer("Num 16-color tex: {}", num_4bit)
    palette_4bit = []
    for _ in range(num_4bit):
        this_pal = {"tex_id": struct.unpack("<I", reader.read(4))[0]}
        this_pal["color_data"] = struct.unpack("16H", reader.read(16*2))
        palette_4bit.append(this_pal)
    return palette_4bit


def read_8bit_palettes(reader):
    # Read 256-color palettes
    num_8bit = struct.unpack("<I", reader.read(4))[0]
    printer("Num 256-color tex: {}", num_8bit)
    palette_8bit = []
    for _ in range(num_8bit):
        this_pal = {"tex_id": struct.unpack("<I", reader.read(4))[0]}
        this_pal["color_data"] = struct.unpack("256H", reader.read(256*2))
        palette_8bit.append(this_pal)
    return palette_8bit


def get_texture_info(reader, filename, num_tex):
    pvr = PSXPVR()
    texture_off = reader.tell()

    pvr.unk = struct.unpack("<I", reader.read(4))[0]
    pvr.pal_size = struct.unpack("<I", reader.read(4))[0]
    pvr.hash = struct.unpack("<I", reader.read(4))[0]
    pvr.index = struct.unpack("<I", reader.read(4))[0]
    pvr.width = struct.unpack("<H", reader.read(2))[0]
    pvr.height = struct.unpack("<H", reader.read(2))[0]

    # 16-bit textures have additional information in their headers
    if(pvr.pal_size == 65536):
        pvr.palette = struct.unpack("<I", reader.read(4))[0]
        pvr.size = struct.unpack("<I", reader.read(4))[0]

    if(fancy_output):
        dimension_string = f"{pvr.width}x{pvr.height}"
        bit_depth_string = f"{int(log2(pvr.pal_size)): >2}-bit"
        palette_string = f"{pvr.palette:#0{3}x}" if pvr.pal_size == 65536 else "N/A"
        print(f"| {num_tex: >7} | {dimension_string: >10} | {bit_depth_string: >9} | {palette_string: >7} | {texture_off:#0{8}x} |")

    return pvr


def get_padding_amount(pvr, pad_width):
    if pvr.height % 2 != 0:
        return 2 if pad_width % 4 != 0 else 0
    else:
        return 0


def extract_4bit_texture(reader, pvr, palette_4bit):
    pad_width = (pvr.width + 0x3) & ~0x3
    pad_width >>= 1
    real_len = (pad_width * pvr.height) + get_padding_amount(pvr, pad_width)
    pal_indices = reader.read(real_len)

    # Find the palette and build the image
    for pal in palette_4bit:
        if pal["tex_id"] == pvr.hash:
            pixels = [None] * (pvr.width * pvr.height)
            for y in range(pvr.height):
                for x in range(pvr.width):
                    color_index = (pal_indices[y * pad_width + (x >> 1)] >> ((x & 0x1) * 4)) & 0xF
                    color = pal["color_data"][color_index]
                    pixel = ps1_to_32bpp(color)
                    pixels[y * pvr.width - x] = pixel
            break
    return pixels


def extract_8bit_texture(reader, pvr, palette_8bit):
    pad_width = (pvr.width + 0x1) & ~0x1
    real_len = (pad_width * pvr.height) + get_padding_amount(pvr, pad_width)
    pal_indices = reader.read(real_len)

    # Find the palette and build the image
    for pal in palette_8bit:
        if pal["tex_id"] == pvr.hash:
            pixels = [None] * (pvr.width * pvr.height)
            for y in range(pvr.height):
                for x in range(pvr.width):
                    color_index = (pal_indices[y * pad_width + x]) & 0xFF
                    color = pal["color_data"][color_index]
                    pixel = ps1_to_32bpp(color)
                    pixels[y * pvr.width - x] = pixel
            break
    return pixels


def update_file_status(ui, file_index, num_actual_tex, textures_written):
    if num_actual_tex > 0:
        ui.fileTable.setItem(file_index, 2, QTableWidgetItem(str(textures_written)))
        if num_actual_tex == textures_written:
            ui.fileTable.setItem(file_index, 3, QTableWidgetItem("OK"))
        else:
            ui.fileTable.setItem(file_index, 3, QTableWidgetItem("ERROR"))
            return False
    else:
        ui.fileTable.setItem(file_index, 3, QTableWidgetItem("SKIPPED"))


def extract_textures(ui, filename, directory, file_index):
    tex_names = []
    tex_hashes = {}
    textures_written = 0

    input_file = os.path.join(directory, filename)

    with open(input_file, "rb") as reader:
        # Read the file header and determine the number of objects, pointer to tagged chunks
        magic = reader.read(4)
        assert magic == b"\x04\x00\x02\x00" or magic == b"\x03\x00\x02\x00" or magic == b"\x06\x00\x02\x00"

        skip_model_data(reader)
        tex_names = read_texture_info(reader)

        # -------------------------------------------------
        # Direct reading from the PSX file - incomplete
        # -------------------------------------------------

        palette_4bit = read_4bit_palettes(reader)
        palette_8bit = read_8bit_palettes(reader)

        num_actual_tex = struct.unpack("<I", reader.read(4))[0]
        ui.fileTable.setItem(file_index, 1, QTableWidgetItem(str(num_actual_tex)))
        printer("Num actual textures: {}", num_actual_tex)

        print_current_position(reader)

        # Skip unknown data
        for i in range(num_actual_tex):
            reader.read(4)

        print_current_position(reader)

        if(num_actual_tex > 0 and fancy_output):
            print(f"Extracting {num_actual_tex} textures from {filename}...")
            print(f"| Texture | Dimensions | Bit-depth | Palette |  Offset  |")

        for i in range(num_actual_tex):
            pvr = get_texture_info(reader, filename, i + 1)
            tex_hashes[i] = tex_names[i]  # tex_hash

            # Now read the raw texture data
            pixels = []

            # Temporary - I plan to make the output a PNG regardless of bit-depth
            if pvr.pal_size != 65536:
                if pvr.pal_size == 16:
                    pixels = extract_4bit_texture(reader, pvr, palette_4bit)
                elif pvr.pal_size == 256:
                    pixels = extract_8bit_texture(reader, pvr, palette_8bit)
                printer("{}: Finished reading texture. I am at: {}", pvr.index, hex(reader.tell()))
                fix_and_write_to_png(ui, filename, pvr.hash, pvr.width, pvr.height, pixels)
                textures_written += 1
            else:
                extract_texture(ui, reader, filename, pvr)
                textures_written += 1
                printer("{}: Finished reading texture. I am at: {}", pvr.index, hex(reader.tell()))

    update_file_status(ui, file_index, num_actual_tex, textures_written)
