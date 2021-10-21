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
        curr_row = []
        for i in reversed(range(i*tex_width, i*tex_width+tex_width)):
            curr_row.extend(pixels[i])
        shifted_right = shift_row_right(curr_row, 1)
        initial_image.append(shifted_right)
    shifted_down = shift_rows_down(initial_image, 1)
    first_col_shifted = shift_col_down(shifted_down, 0, -1, tex_height)
    return first_col_shifted
