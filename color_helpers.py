# Alpha is either 0 or 128 for some reason
argb1555_params = {
    "red_mask": 0x7C00,
    "green_mask": 0x3E0,
    "blue_mask": 0x1F,
    "alpha_mask": 0x8000,

    "red_max": 31,
    "green_max": 31,
    "blue_max": 31,
    "alpha_max": 1,

    "alpha_shift": 15,
    "red_shift": 10,
    "green_shift": 5,
}

# 565
rgb565_params = {
    "red_mask": 0xF800,
    "green_mask": 0x7E0,
    "blue_mask": 0x1F,
    "alpha_mask": 0,

    "red_max": 31,
    "green_max": 63,
    "blue_max": 31,
    "alpha_max": 0,

    "alpha_shift": 16,
    "red_shift": 11,
    "green_shift": 5,
}

# 4444
argb4444_params = {
    "red_mask": 0xF00,
    "green_mask": 0xF0,
    "blue_mask": 0xF,
    "alpha_mask": 0xF000,

    "red_max": 15,
    "green_max": 15,
    "blue_max": 15,
    "alpha_max": 15,

    "alpha_shift": 12,
    "red_shift": 8,
    "green_shift": 4,
}


def ps1_to_32bpp(color):
    r = (color) & 0x1F
    g = (color >> 5) & 0x1F
    b = (color >> 10) & 0x1F
    a = (color >> 15) & 0x1

    if r == 31 and g == 0 and b == 31:
        # Fully transparent
        return [0, 0, 0, 0]
    else:
        return [int((r/31)*255), int((g/31)*255), int((b/31)*255), 255]


def get_16bpp_color_params(palette):
    # 5551
    # Alpha is either 0 or 128 for some reason

    if palette & 0xF == 0:
        return argb1555_params

    # 565
    elif palette & 0xF == 1:
        return rgb565_params

    # 4444
    else:
        return argb4444_params


def convert_16bpp_to_32bpp(params, color):
    r = (color & params["red_mask"]) >> params["red_shift"]
    g = (color & params["green_mask"]) >> params["green_shift"]
    b = (color & params["blue_mask"])
    a = (color & params["alpha_mask"]) >> params["alpha_shift"]

    r = int((r / params["red_max"]) * 255)
    g = int((g / params["green_max"]) * 255)
    b = int((b / params["blue_max"]) * 255)

    a = 255 if params["alpha_max"] == 0 else int((a / params["alpha_max"]) * 255)

    return [r, g, b, a]
