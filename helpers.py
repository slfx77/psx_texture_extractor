import os

from PIL import Image

import png


class Printer(object):
    def __init__(self):
        self.on = True

    def __call__(self, message, *stuff):
        if self.on:
            print(message.format(*stuff))
        return stuff[0]


##################################
# IO THPS Scene Image Correction #
##################################


def shift_row_right(row, amount):
    shifted_right = []
    shifted_right.extend(row[amount * -4 :])
    shifted_right.extend(row[0 : amount * -4])
    return shifted_right


def shift_rows_down(image, amount):
    new_image = image.copy()
    for _ in range(amount):
        shifted_down = []
        shifted_down.append(new_image[-1])
        shifted_down.extend(new_image[0:-1])
        new_image = shifted_down
    return new_image


def shift_col_down(image, col, amount, height):
    col_to_shift = []
    col_start = col * 4
    for i in range(0, height):
        col_to_shift.extend(image[i][col_start : col_start + 4])
    col_shifted_up = shift_row_right(col_to_shift, amount)
    new_image = []
    for i in range(0, height):
        if col != 0:
            new_image.append(image[i][0:col_start])
        else:
            new_image.append([])
        new_image[i].extend(col_shifted_up[i * 4 : i * 4 + 4])
        new_image[i].extend(image[i][col_start + 4 :])
    return new_image


def fix_pixel_data(width, height, pixels):
    initial_image = []
    for i in range(0, height):
        cur_row = []
        for i in reversed(range(i * width, (i + 1) * width)):
            cur_row.extend(pixels[i])
        shifted_right = shift_row_right(cur_row, 1)
        initial_image.append(shifted_right)
    shifted_down = shift_rows_down(initial_image, 1)
    return shift_col_down(shifted_down, 0, -1, height)


def write_to_png(worker, filename, output_dir, create_sub_dirs, pvr, pixels):
    postprocess = False
    final_image = pixels
    worker.file_extracted_signal.emit()
    filename_without_extension = "".join(filename.split(".")[0:-1])

    if create_sub_dirs:
        output_dir = os.path.join(output_dir, filename_without_extension)
    else:
        output_dir = output_dir

    output_path = os.path.join(output_dir, f"{filename_without_extension}_{pvr.header_offset:#0{8}x}.png")

    if pvr.pal_size != 65536:
        final_image = fix_pixel_data(pvr.width, pvr.height, pixels)
    elif (pvr.palette & 0xFF00) in [0x100, 0xD00]:
        postprocess = True
    elif (pvr.palette & 0xFF00) == 0x400:
        output_path = output_path[0:-4] + "_i" + output_path[-4:]  # Mark unsupported textures with _i

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    file = open(output_path, "wb")
    writer = png.Writer(pvr.width, pvr.height, greyscale=False, alpha=True)
    writer.write(file, final_image)
    file.close()

    if postprocess:
        texture = Image.open(output_path)
        out = texture.rotate(270, expand=True)
        out = out.transpose(Image.FLIP_LEFT_RIGHT)
        out.save(output_path)
