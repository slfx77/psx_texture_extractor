import rawtex_options
import struct


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
    nums = [None] * 4

    nums[0] = 1
    nums[1] = 808540228
    nums[2] = rawtex_options.pixbl[texture_type_index]
    nums[3] = rawtex_options.bpp[texture_type_index] * 2
    if (nums[2] == 1):
        nums[3] = rawtex_options.bpp[texture_type_index] / 8
    if (texture_type_index == 71):
        nums[1] = 827611204
    if (texture_type_index == 74):
        nums[1] = 861165636
    if (texture_type_index == 77):
        nums[1] = 894720068
    if (texture_type_index == 80):
        nums[1] = 826889281
    if (texture_type_index == 83):
        nums[1] = 843666497

    for index, num in enumerate(nums):
        nums[index] = int(num)

    return nums


def do_convert(reader, pvr):
    texture_type_index = rawtex_options.texture_type.index("b5g6r5_unorm")
    nums = get_nums(texture_type_index)

    sy = int(pvr.height / nums[2])
    sx = int(pvr.width / nums[2])
    texture_buffer_size = (sx * sy * nums[3])
    texture_buffer = [0x00] * texture_buffer_size

    for i in range(sx * sy):
        next_index = morton(i, sx, sy)
        channel = struct.unpack("<H", reader.read(nums[3]))[0]
        destination_index = int(nums[3] * next_index / 2)
        texture_buffer[destination_index] = channel

    return texture_buffer
