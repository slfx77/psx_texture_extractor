import os
import png

from fix_ps1_texures import fix_pixel_data


def write_to_png(ui, filename, tex_hash, tex_width, tex_height, pixels):
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
