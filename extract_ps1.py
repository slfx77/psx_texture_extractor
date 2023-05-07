from color_helpers import ps1_to_32bpp


def get_padding_amount(pvr, pad_width):
    if pvr.height % 2 != 0:
        return 2 if pad_width % 4 != 0 else 0
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
