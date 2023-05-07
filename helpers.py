import os

import png

##################################
# IO THPS Scene Image Correction #
##################################


def shift_row_pixels(row_pixels, shift_amount):
    shifted_row = []
    shifted_row.extend(row_pixels[shift_amount * -4 :])
    shifted_row.extend(row_pixels[0 : shift_amount * -4])
    return shifted_row


def shift_image_rows(image_data, shift_amount):
    shifted_image = image_data.copy()
    for _ in range(shift_amount):
        new_rows = []
        new_rows.append(shifted_image[-1])
        new_rows.extend(shifted_image[0:-1])
        shifted_image = new_rows
    return shifted_image


def shift_image_column(image_data, col_index, shift_amount, image_height):
    column_data = []
    col_start_index = col_index * 4
    for row_index in range(image_height):
        column_data.extend(image_data[row_index][col_start_index : col_start_index + 4])
    shifted_column = shift_row_pixels(column_data, shift_amount)
    new_image_data = []
    for row_index in range(image_height):
        if col_index != 0:
            new_image_data.append(image_data[row_index][0:col_start_index])
        else:
            new_image_data.append([])
        new_image_data[row_index].extend(shifted_column[row_index * 4 : row_index * 4 + 4])
        new_image_data[row_index].extend(image_data[row_index][col_start_index + 4 :])
    return new_image_data


def fix_pixel_data(width, height, pixels):
    initial_image = []
    for row in range(0, height):
        cur_row = []
        for col in reversed(range(row * width, (row + 1) * width)):
            cur_row.extend(pixels[col])
        shifted_right = shift_row_pixels(cur_row, 1)
        initial_image.append(shifted_right)
    shifted_down = shift_image_rows(initial_image, 1)
    return shift_image_column(shifted_down, 0, -1, height)


def write_to_png(filename, output_dir, create_sub_dirs, pvr, pixels):
    final_image = pixels
    filename_without_extension = "".join(filename.split(".")[0:-1])

    if create_sub_dirs:
        output_dir = os.path.join(output_dir, filename_without_extension)

    output_path = os.path.join(output_dir, f"{filename_without_extension}_{pvr.header_offset:#0{8}x}.png")

    if pvr.pal_size != 65536:
        final_image = fix_pixel_data(pvr.width, pvr.height, pixels)
    elif (pvr.palette & 0xFF00) == 0x400:
        output_path = output_path[0:-4] + "_i" + output_path[-4:]  # Mark unsupported textures with _i
    elif (pvr.palette & 0xFF00) == 0x200:
        output_path = output_path[0:-4] + "_d" + output_path[-4:]  # Mark unsupported textures with _d

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    output_file = open(output_path, "wb")
    writer = png.Writer(pvr.width, pvr.height, greyscale=False, alpha=True)
    writer.write(output_file, final_image)
    output_file.close()
