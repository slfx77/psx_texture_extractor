class PSXPVR:
    # An unknown value, possibly a header or some format-specific information.
    unk = 0

    # The size of the color palette, which determines the bit depth of the texture.
    pal_size = 0

    # A hash value associated with the texture.
    hash = 0

    # The index of the texture in the file.
    index = 0

    # The width of the texture in pixels.
    width = 0

    # The height of the texture in pixels.
    height = 0

    # The palette index for 16-bit textures.
    palette = 0

    # The size of the texture data in bytes for 16-bit textures.
    size = 0

    # Extra data (not part of the format but used for conversion)
    # The offset in the file where the texture's header is located.
    header_offset = 0

    # The offset in the file where the texture's data is located.
    texture_offset = 0
