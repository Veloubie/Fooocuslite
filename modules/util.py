import numpy as np
import datetime
import random
import os

from PIL import Image


def image_is_generated_in_current_ui(image, ui_width, ui_height):
    H, W, C = image.shape

    if H < ui_height:
        return False

    if W < ui_width:
        return False

    # k1 = float(H) / float(W)
    # k2 = float(ui_height) / float(ui_width)
    # d = abs(k1 - k2)
    #
    # if d > 0.01:
    #     return False

    return True


LANCZOS = (Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)


def resample_image(im, width, height):
    im = Image.fromarray(im)
    im = im.resize((width, height), resample=LANCZOS)
    return np.array(im)


def resize_with_default_mode(im, width, height, resize_mode):
    if resize_mode != 1:
        return None
    ratio = width / height
    src_ratio = im.width / im.height
    src_w = width if ratio > src_ratio else im.width * height // im.height
    src_h = height if ratio <= src_ratio else im.height * width // im.width
    resized = im.resize((src_w, src_h), resample=LANCZOS)
    res = Image.new("RGB", (width, height))
    res.paste(resized, box=(width // 2 - src_w // 2, height // 2 - src_h // 2))
    return res


def resize_with_last_mode(im, width, height):
    ratio = width / height
    src_ratio = im.width / im.height

    src_w = width if ratio < src_ratio else im.width * height // im.height
    src_h = height if ratio >= src_ratio else im.height * width // im.width

    resized = im.resize((src_w, src_h), resample=LANCZOS)
    res = Image.new("RGB", (width, height))
    res.paste(resized, box=(width // 2 - src_w // 2, height // 2 - src_h // 2))

    if ratio < src_ratio:
        fill_height = height // 2 - src_h // 2
        if fill_height > 0:
            res.paste(resized.resize((width, fill_height), box=(0, 0, width, 0)), box=(0, 0))
            res.paste(resized.resize((width, fill_height), box=(0, resized.height, width, resized.height)),
                      box=(0, fill_height + src_h))
    elif ratio > src_ratio:
        fill_width = width // 2 - src_w // 2
        if fill_width > 0:
            res.paste(resized.resize((fill_width, height), box=(0, 0, 0, height)), box=(0, 0))
            res.paste(resized.resize((fill_width, height), box=(resized.width, 0, resized.width, height)),
                      box=(fill_width + src_w, 0))
    return res


def resize_image(im, width, height, resize_mode=1):
    """
    Resizes an image with the specified resize_mode, width, and height.

    Args:
        resize_mode: The mode to use when resizing the image.
            0: Resize the image to the specified width and height.
            1: Resize the image to fill the specified width and height, maintaining the aspect ratio, and then center the image within the dimensions, cropping the excess.
            2: Resize the image to fit within the specified width and height, maintaining the aspect ratio, and then center the image within the dimensions, filling empty with data from image.
        im: The image to resize.
        width: The width to resize the image to.
        height: The height to resize the image to.
    """
    im = Image.fromarray(im)
    result = im.resize((width, height), resample=LANCZOS)
    if resize_mode != 0:
        result = resize_with_default_mode(im, width, height, resize_mode)
        if result is None:
            result = resize_with_last_mode(im, width, height)
    return np.array(result)


def make_sure_that_image_is_not_too_large(x):
    H, W, C = x.shape
    k = float(2048 * 2048) / float(H * W)
    k = k ** 0.5
    if k < 1:
        H_new = int(H * k)
        W_new = int(W * k)
        print(f'Image is too large - resizing from ({H}, {W}) to ({H_new}, {W_new}).')
        x = resize_image(x, width=W_new, height=H_new, resize_mode=0)
    return x


def HWC3(x):
    assert x.dtype == np.uint8
    if x.ndim == 2:
        x = x[:, :, None]
    assert x.ndim == 3
    H, W, C = x.shape
    assert C == 1 or C == 3 or C == 4
    if C == 3:
        return x
    if C == 1:
        return np.concatenate([x, x, x], axis=2)
    if C == 4:
        color = x[:, :, 0:3].astype(np.float32)
        alpha = x[:, :, 3:4].astype(np.float32) / 255.0
        y = color * alpha + 255.0 * (1.0 - alpha)
        y = y.clip(0, 255).astype(np.uint8)
        return y


def remove_empty_str(items, default=None):
    items = [x for x in items if x != ""]
    if len(items) == 0 and default is not None:
        return [default]
    return items


def join_prompts(*args, **kwargs):
    prompts = [str(x) for x in args if str(x) != ""]
    if len(prompts) == 0:
        return ""
    if len(prompts) == 1:
        return prompts[0]
    return ', '.join(prompts)


def generate_temp_filename(folder='./outputs/', extension='png'):
    current_time = datetime.datetime.now()
    date_string = current_time.strftime("%Y-%m-%d")
    time_string = current_time.strftime("%Y-%m-%d_%H-%M-%S")
    random_number = random.randint(1000, 9999)
    filename = f"{time_string}_{random_number}.{extension}"
    result = os.path.join(folder, date_string, filename)
    return date_string, os.path.abspath(os.path.realpath(result)), filename


def get_files_from_folder(folder_path, exensions=None, name_filter=None):
    if not os.path.isdir(folder_path):
        raise ValueError("Folder path is not a valid directory.")

    filenames = []

    for root, dirs, files in os.walk(folder_path):
        relative_path = os.path.relpath(root, folder_path)
        if relative_path == ".":
            relative_path = ""
        for filename in files:
            _, file_extension = os.path.splitext(filename)
            if (exensions == None or file_extension.lower() in exensions) and (name_filter == None or name_filter in _):
                path = os.path.join(relative_path, filename)
                filenames.append(path)

    return sorted(filenames, key=lambda x: -1 if os.sep in x else 1)
