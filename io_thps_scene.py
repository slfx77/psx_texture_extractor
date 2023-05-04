import os
import struct
from math import log2

from color_helpers import ps1_to_32bpp
from extract_psx import extract_16bit_texture
from helpers import Printer, write_to_png
from psx_pvr import PSXPVR

printer = Printer()
printer.on = False
fancy_output = True


def print_current_position(reader, output_strings):
    if printer.on:
        output_strings.append(f"I am at: {hex(reader.tell())}")


def skip_model_data(reader, output_strings):
    (ptr_meta, obj_count) = struct.unpack("<II", reader.read(8))
    if printer.on:
        output_strings.append(f"Num objects: {obj_count}")

    # "Objects" are 36 bytes. Skip over them for reading textures.
    for _ in range(obj_count):
        # Skip over object data
        reader.read(36)

    # Determine number of meshes (we need to skip over the mesh name list before texture info)
    mesh_count = struct.unpack("<I", reader.read(4))[0]
    if printer.on:
        output_strings.append(f"Num meshes: {mesh_count}")

    # Skip to the tagged chunks, find the textures
    reader.seek(ptr_meta)
    chunk_count = -1
    while True:
        magic = reader.read(4)
        chunk_count += 1
        if magic != b"\xFF\xFF\xFF\xFF":
            if printer.on:
                output_strings.append(f"SKIPPED CHUNK: 0x{ magic.hex()}")
            unk_length = struct.unpack("<I", reader.read(4))[0]
            reader.read(unk_length)
            if chunk_count > 16:
                # There should not be this many tagged chunks, must be a file error
                raise Exception("Unable to parse PSX texture library, cannot find texture data")
        else:
            if printer.on:
                output_strings.append(f"END OF TAGGED CHUNKS")
            break

    # Now we are at the model names list - if there are any models
    for _ in range(mesh_count):
        reader.read(4)


def read_texture_info(reader, output_strings):
    # Print position where texture data starts
    print_current_position(reader, output_strings)

    # Read number of textures
    num_tex = struct.unpack("<I", reader.read(4))[0]
    if printer.on:
        output_strings.append(f"Num textures: {num_tex}")

    tex_names = []
    for _ in range(num_tex):
        tex_names.append(struct.unpack("<I", reader.read(4))[0])
    return tex_names


def read_palettes(reader, output_strings, num_colors):
    num_textures = struct.unpack("<I", reader.read(4))[0]
    if printer.on:
        output_strings.append(f"Num {num_colors}-color tex: {num_textures}")
    palettes = []
    for _ in range(num_textures):
        this_pal = {"tex_id": struct.unpack("<I", reader.read(4))[0]}
        this_pal["color_data"] = struct.unpack(f"{num_colors}H", reader.read(num_colors * 2))
        palettes.append(this_pal)
    return palettes


def get_texture_info(reader, output_strings, num_tex):
    pvr = PSXPVR()
    pvr.header_offset = reader.tell()

    pvr.unk = struct.unpack("<I", reader.read(4))[0]
    pvr.pal_size = struct.unpack("<I", reader.read(4))[0]
    pvr.hash = struct.unpack("<I", reader.read(4))[0]
    pvr.index = struct.unpack("<I", reader.read(4))[0]
    pvr.width = struct.unpack("<H", reader.read(2))[0]
    pvr.height = struct.unpack("<H", reader.read(2))[0]

    # 16-bit textures have additional information in their headers
    if pvr.pal_size == 65536:
        pvr.palette = struct.unpack("<I", reader.read(4))[0]
        pvr.size = struct.unpack("<I", reader.read(4))[0]

    pvr.texture_offset = reader.tell()

    if fancy_output:
        bit_depth_string = f"{int(log2(pvr.pal_size)): >2}-bit"
        palette_string = f"{pvr.palette:#0{3}x}" if pvr.pal_size == 65536 else "N/A"
        output_strings.append(f"| {num_tex: >7} | {pvr.width: >5} | {pvr.height: >6} | {bit_depth_string: >9} | {palette_string: >7} | {pvr.header_offset:#0{8}x} |")

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


def extract_textures(filename, input_dir, output_dir, index, create_sub_dirs, output_strings, update_file_table, update_file_status):
    tex_names = []
    tex_hashes = {}
    textures_written = 0

    extraction_functions = {
        16: lambda reader, pvr: extract_4bit_texture(reader, pvr, palette_4bit),
        256: lambda reader, pvr: extract_8bit_texture(reader, pvr, palette_8bit),
        65536: lambda reader, pvr: extract_16bit_texture(reader, pvr, output_strings),
    }

    input_file = os.path.join(input_dir, filename)

    with open(input_file, "rb") as reader:
        # Read the file header and determine the number of objects, pointer to tagged chunks
        magic = reader.read(4)
        assert magic == b"\x04\x00\x02\x00" or magic == b"\x03\x00\x02\x00" or magic == b"\x06\x00\x02\x00"

        skip_model_data(reader, output_strings)
        tex_names = read_texture_info(reader, output_strings)

        # ----------------------------------------------------------------------------------------------
        # Direct reading from the PSX file - Mostly complete, 16-bit palettes 0x400 - 0x402 unsupported
        # ----------------------------------------------------------------------------------------------

        palette_4bit = read_palettes(reader, output_strings, 16)
        palette_8bit = read_palettes(reader, output_strings, 256)

        num_actual_tex = struct.unpack("<I", reader.read(4))[0]
        update_file_table(index, 1, str(num_actual_tex))
        if printer.on:
            output_strings.append(f"Num actual textures: {num_actual_tex}")

        print_current_position(reader, output_strings)

        # Skip unknown data
        for i in range(num_actual_tex):
            reader.read(4)

        print_current_position(reader, output_strings)

        if num_actual_tex > 0 and fancy_output:
            output_strings.append(f"Extracting {num_actual_tex} textures from {filename}...")
            output_strings.append(f"| Texture | Width | Height | Bit-depth | Palette |  Offset  |")

        for i in range(num_actual_tex):
            pvr = get_texture_info(reader, output_strings, i + 1)
            tex_hashes[i] = tex_names[i]  # tex_hash

            # Now read the raw texture data
            pixels = []

            extraction_function = extraction_functions.get(pvr.pal_size)
            if extraction_function:
                pixels = extraction_function(reader, pvr)
            elif printer.on:
                output_strings.append(f"Unsupported palette size ({pvr.pal_size}) for texture {i + 1}")

            if printer.on:
                output_strings.append(f"{pvr.index}: Finished reading texture. I am at: {hex(reader.tell())}")
            # Replace the call to write_to_png with the updated version
            write_to_png(filename, output_dir, create_sub_dirs, pvr, pixels)
            textures_written += 1

    update_file_status(index, num_actual_tex, textures_written)
