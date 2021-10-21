import os
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
    shifted_right.extend(row[amount*-4:])
    shifted_right.extend(row[0:amount*-4])
    return shifted_right


def shift_rows_down(image, amount):
    new_image = image.copy()
    for _ in range(amount):
        shifted_down = []
        shifted_down.append(new_image[-1])
        shifted_down.extend(new_image[0:-1])
        new_image = shifted_down
    return new_image


def shift_col_down(image, col, amount, tex_height):
    col_to_shift = []
    col_start = col * 4
    for i in range(0, tex_height):
        col_to_shift.extend(image[i][col_start:col_start+4])
    col_shifted_up = shift_row_right(col_to_shift, amount)
    new_image = []
    for i in range(0, tex_height):
        if col != 0:
            new_image.append(image[i][0:col_start])
        else:
            new_image.append([])
        new_image[i].extend(col_shifted_up[i*4:i*4+4])
        new_image[i].extend(image[i][col_start+4:])
    return new_image


def fix_pixel_data(tex_width, tex_height, pixels):
    initial_image = []
    for i in range(0, tex_height):
        cur_row = []
        for i in reversed(range(i * tex_width, (i + 1) * tex_width)):
            cur_row.extend(pixels[i])
        shifted_right = shift_row_right(cur_row, 1)
        initial_image.append(shifted_right)
    shifted_down = shift_rows_down(initial_image, 1)
    return shift_col_down(shifted_down, 0, -1, tex_height)


def fix_and_write_to_png(ui, filename, tex_hash, tex_width, tex_height, pixels):
    ui.files_extracted += 1
    filename_without_extension = "".join(filename.split(".")[0:-1])

    if ui.create_sub_dirs:
        output_dir = os.path.join(ui.output_dir, filename_without_extension)
    else:
        output_dir = ui.output_dir

    output_path = os.path.join(output_dir, f"{filename_without_extension}_{tex_hash:#0{8}x}{ui.files_extracted}.png")
    converted_pixels = fix_pixel_data(tex_width, tex_height, pixels)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    file = open(output_path, 'wb')
    writer = png.Writer(tex_width, tex_height, greyscale=False, alpha=True)
    writer.write(file, converted_pixels)
    file.close()
