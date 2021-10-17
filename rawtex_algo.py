import rawtex_options
import struct

from os import SEEK_CUR


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


def get_nums(texture_type_index):
    num1 = 1
    num2 = 808540228
    num3 = rawtex_options.pixbl[texture_type_index]
    num4 = rawtex_options.bpp[texture_type_index] * 2
    if (num3 == 1):
        num4 = rawtex_options.bpp[texture_type_index] / 8
    if (texture_type_index == 71):
        num2 = 827611204
    if (texture_type_index == 74):
        num2 = 861165636
    if (texture_type_index == 77):
        num2 = 894720068
    if (texture_type_index == 80):
        num2 = 826889281
    if (texture_type_index == 83):
        num2 = 843666497

    return[num1, num2, num3, num4]


def do_convert(reader, pvr, filename):
    texture_type_index = rawtex_options.texture_type.index("b5g6r5_unorm")
    nums = get_nums(texture_type_index)

    texture_buffer = [0x00] * (pvr.size * 4)
    # color_buffer = [0x00] * 16
    sy = int(pvr.height / nums[2])
    sx = int(pvr.width / nums[2])

    for i in range(sx * sy):
        color_index = morton(i, sx, sy)
        color = struct.unpack("<H", reader.read(2))[0]
        destination_index = int(nums[3] * color_index)
        texture_buffer[destination_index] = color
    print("Skipped {}!", filename)
