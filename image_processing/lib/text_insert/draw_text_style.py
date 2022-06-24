import os
import random
import json
import configparser
import textwrap

from PIL import Image, ImageFont, ImageDraw
from datetime import datetime

# Load file config
config = configparser.RawConfigParser()

try:
    config.read('config.cfg')
    details_dict = dict(config.items('CONFIG_IMAGE'))

except:
    print("Run in test environment")
    print(os.path.isfile('../../../config.cfg'))
    config.read('../../../config.cfg')
    details_dict = dict(config.items('CONFIG_IMAGE'))


# Get two param max width and max height from config file
H, W = int(details_dict['height']), int(details_dict['width'])
MAX_DIGIT = int(details_dict['max_digit_text'])
MIN_DIGIT = int(details_dict['min_digit_text'])
OFF_SET = int(details_dict['off_set'])
HEIGHT_OFFSET = int(details_dict['height_offset'])
WIDTH_OFFSET = int(details_dict['width_offset'])
DISTANCE_LINE = int(details_dict['distance_line'])
HEIGHT_OFF_SONG = int(details_dict['height_off_song'])
EDGE_OFFSET = int(details_dict["edge_offset"])
WIDTH_LINE = int(details_dict["width_line"])
LONG_WIDTH = int(details_dict["long_width"])
OFFSET_TEXT = int(details_dict["offset_text"])


# Width center alignment
def _width_center(width_text, width_img):
    if width_text >= width_img:
        return False
    return int((width_img - width_text) / 2) if (width_img - width_text) > 0 else False


def _get_font(path):
    """

    :param path:
    :return:
    """
    if os.path.isfile(path) is False:
        print(f'{path} found font folder')
        return False

    if path.lower().endswith(('.ttf', '.otf')) is False:
        print(f"{path} format not true")
        return False
    return path


def _get_new_size(width_ob, height_ob):
    """
    Detail: To fit image into config size
    :param width: width of image
    :param height: height of image
    :return: new size for image
    """

    # Check size of image background with size object
    if width_ob > W or height_ob > H:
        div = max(width_ob / W, height_ob / H)
        width_ob = int(width_ob / div)
        height_ob = int(height_ob / div)
    else:
        return False

    return width_ob, height_ob


# Get the number of song:
def _get_number(i):
    i += 1
    num = str(i)
    if len(num) < 2:
        num = str(f"0{i}")

    return num


def _get_color(color, transparent_value):
    if len(color) != 3:
        return False
    color = list(color)
    color.append(transparent_value)
    color = tuple(color)
    return color


# Get region of the text
def _text_region(width, height, width_text, height_text):
    # print(f"{width}*{height}*{width_text}*{height_text}")
    top = height
    right = width + width_text if (width_text + width) < W else W
    bottom = height + height_text if (height + height_text) < H else H
    left = width
    return left, top, right, bottom


def draw_one_col_no_singer(im_ob, text_region, path_output, js_txt, debug=False):
    """

    :param im_ob:
    :param text_region:
    :param path_output:
    :param js_txt:
    :param debug:
    :return:
    """

    # To create new variable
    result = dict()
    result["status"] = "error"
    result["content"] = ''
    result["data"] = []
    result["image_false"] = ''

    # check conditional
    if os.path.isdir(path_output) is False:
        print(f"Cannot find {path_output}")
        result["content"] = f"Cannot find {path_output}"
        return result

    if len(text_region) != 4:
        print("Text region format not true")
        result["content"] = "Text region format not true"
        return result

    if js_txt is None:
        print("No json file import")
        result["content"] = "No json file import"
        return result

    try:
        sum = js_txt["sum"]
        list_song = js_txt["list_songs"]
        align = js_txt["align"]
        color = js_txt["color_song"]
        size_txt = js_txt["size_txt"]
        path_font_song = js_txt["path_font_song"]

        if len(list_song) != sum:
            print("Data is wrong")
            result["content"] = "Data is wrong"
            return result
    except Exception as error:
        print(error)
        result["content"] = error
        return result

    if align not in ["center", "left", "right"]:
        result["content"] = "align must be in [center, left, right]"
        return result

    # Get color to draw text
    color = _get_color(color, 255)

    if color is False:
        result["content"] = "color format is not right"
        return result

    # Get font song
    font_song = _get_font(path_font_song)

    if font_song is False:
        print("Font file or folder not found!")
        result["content"] = "Font file or folder not found or format not True!"
        return result

    im = Image.open(im_ob).convert('RGBA')
    width_img, height_img = im.size

    new_size = _get_new_size(width_img, height_img)
    if new_size is False:
        pass
    else:
        width_img, height_img = new_size
        # Test case
        new_size = (1280, 720)
        im = im.resize(new_size)

    # Adjust text region
    _width_title_ = text_region[0]
    _title_status = False
    _title_change_status = False

    _text_position = "left"
    if text_region[0] > W/3:
        _text_position = "right"

    try:
        title = js_txt["title"]
        font_title = js_txt["path_font_title"]
        size_title = js_txt["size_title"]
        _color_title = js_txt["color_title"]
        color_title = _get_color(_color_title, 255)
        if color_title is False:
            result["content"] = f"{color_title} format is not True"
            return result
        title_region = text_region
        # make a blank image for the text, initialized to transparent text color
        txt = Image.new('RGBA', im.size, (255, 255, 255, 0))

        # Get param of title
        fnt = ImageFont.truetype(font_title, size_title)
        # get a drawing context
        d = ImageDraw.Draw(txt)
        width_title, height_title = d.textsize(title, font=fnt, spacing=HEIGHT_OFFSET)
        _width_text_region = text_region[2] - text_region[0]
        width = _width_center(width_text=width_title, width_img=_width_text_region)

        # To expand text region
        if width is False:
            _title_change_status = True
            _width_text_region += OFFSET_TEXT
            width = _width_center(width_text=width_title, width_img=_width_text_region)

        # If width is False, auto resize size of title
        while width is False:
            size_title -= 1
            # Get a font
            fnt = ImageFont.truetype(font_title, size_title)
            width_title, height_title = d.textsize(title, font=fnt, spacing=HEIGHT_OFFSET)
            width = _width_center(width_text=width_title, width_img=_width_text_region)

        # Set new width position for title
        _width_title_ += width

        # height_offset_song = height_title * 1.5 + 2 * WIDTH_LINE
        height_offset_song = height_title + 6 * WIDTH_LINE

        # Set title status is True
        _title_status = True

    except:
        title = False
        height_offset_song = 2 * WIDTH_LINE

    # Adjust parameter text region
    text_region = list(text_region)
    text_region[1] = int(text_region[1]) + height_offset_song

    # make a blank image for the text, initialized to transparent text color
    txt = Image.new('RGBA', im.size, (255, 255, 255, 0))

    _fnt_song = ImageFont.truetype(font_song, size_txt)
    _d_song = ImageDraw.Draw(txt)
    _width_text, _height_text = _d_song.textsize('test', font=_fnt_song)
    del _d_song, txt

    space_line = int(0.8 * _height_text)

    txt = Image.new('RGBA', im.size, (255, 255, 255, 0))

# Draw song into image
    # Create new param
    max_width = 0   # The max long of list song
    height_song_top = int(text_region[1]) + 10  # The coordinate height song top
    height_song_bottom = int(text_region[3])    # The coordinate height song bottom
    width_song = int(text_region[0])    # The list coordinate of width song fl collum
    # _with_song = int(((text_region[2]) - text_region[0]) / 3) + text_region[0]

    fnt = ImageFont.truetype(font_song, size_txt)
    # get a drawing content
    d = ImageDraw.Draw(txt)

    song_str = {}
    stop = False
    # The song number
    j = 0
    sum_song_one_col = 0
    count_img = 0
    _list_song = list_song.copy()
    _tmp_index = 0

    for _index, song in enumerate(_list_song):
        _song_str = f"{_get_number(_index)}. {song['name']}\n"
        width_text, height_text = d.textsize(_song_str, font=fnt, spacing=space_line)
        if width_text >= (text_region[2] - text_region[0] - 2 * EDGE_OFFSET):
            list_song.pop(_tmp_index)
            _tmp_index -= 1
        _tmp_index += 1

    if debug:
        print(list_song)

    # List to save max width for every image
    list_max_width_img = []

    while j < len(list_song):  # Not finish list

        # To save list song follow collum
        song_str[f'img_{count_img}'] = []
        song_str[f'list_song_{count_img}'] = ''

        # clear height before to use
        height_text = 0

        while (height_song_bottom - height_song_top - height_text) > 0:  # Check end of the height image
            # Calculator width of image count_img
            song_str[f'img_{count_img}'].append(list_song[j]['name'])
            song_str[f'list_song_{count_img}'] += f"{_get_number(j)}. {list_song[j]['name']}\n"
            width_text, height_text = d.textsize(f"{song_str[f'list_song_{count_img}']}\n",
                                                 font=fnt, spacing=space_line)
            max_width = width_text if width_text > max_width else max_width
            if stop is False:
                sum_song_one_col += 1
            j += 1
            if j >= len(list_song):
                break

        if stop is False:
            stop = True

        # Get max value of width song
        list_max_width_img.append(max_width)
        max_width = 0
        # Add 1 count image
        count_img += 1

        if count_img == int(len(list_song) // sum_song_one_col):
            break

    list_width_coordinate = []

    for _max_width in list_max_width_img:
        list_width_coordinate.append((width_song + text_region[2] - _max_width) // 2)

    if debug:
        print(f"width_song is {width_song}")
        print(f"song_str is {song_str}")

# Draw song into the picture
    warring_status = False
    for img in range(count_img):
        txt = Image.new('RGBA', im.size, (255, 255, 255, 0))
        fnt = ImageFont.truetype(font_song, size_txt)

        # get a drawing content
        d = ImageDraw.Draw(txt)
        d.multiline_text((list_width_coordinate[img], height_song_top),
                         text=song_str[f'list_song_{img}'], font=fnt, fill=color,
                         align=align, spacing=space_line)

        if title is False:
            pass
        else:
            width = _width_center(width_text=width_title, width_img=_width_text_region)
            if _text_position == "right":
                width += text_region[0] - OFFSET_TEXT
            else:
                width += text_region[0]
            if debug:
                print("Width is ", width)
            d = ImageDraw.Draw(txt)
            fnt = ImageFont.truetype(font_title, size_title)
            width_text, height_text = d.textsize(title, font=fnt)
            # Set height in top off image
            height = title_region[1] + 10 if title_region[1] == 0 else title_region[1]
            # Draw underline and tile:

            coordinate_txt = (width, height)
            d.multiline_text(coordinate_txt, text=title, font=fnt, fill=color_title,
                             align='center', spacing=HEIGHT_OFFSET)
        if debug:
            txt.show()

        _im_tmp = im.copy()
        out = Image.alpha_composite(_im_tmp, txt)
        if debug:
            out.show()

        time = datetime.now()
        current_time = time.strftime("%H:%M:%S:%f")
        current_date = time.date()

        path_new = f"{path_output}/{current_date}_{current_time}.png"

        try:
            out.save(path_new)
        except Exception as error:
            print(error)
            warring_status = True
            result["content"] += f"{error}\n"
            continue
        _tmp_dict = {
            "path_img": path_new,
            "list_songs": song_str[f'img_{img}']
        }
        result["data"].append(_tmp_dict)

    if warring_status:
        result["status"] = "warring"
    else:
        if len(result["data"]) == 0:
            result["status"] = "error"
            result["content"] = "song not enough for draw two collum"
        else:
            result["status"] = "success"

    # del out, time, current_time, current_date, fnt, im

    return result


def draw_double_col(im_ob, text_region, path_output, js_txt, debug=False):
    """
Detail: This to draw in image with style no singer and two collum
    :param im_ob:
    :param text_region:
    :param path_output:
    :param js_txt:
    :param debug:
    :return:
    """

    # To create new variable
    result = dict()
    result["status"] = "error"
    result["content"] = ''
    result["data"] = []
    result["image_false"] = ''

    # check conditional
    if os.path.isdir(path_output) is False:
        print(f"Cannot find {path_output}")
        result["content"] = f"Cannot find {path_output}"
        return result

    if len(text_region) != 4:
        print("Text region format not true")
        result["content"] = "Text region format not true"
        return result

    if js_txt is None:
        print("No json file import")
        result["content"] = "No json file import"
        return result

    try:
        sum = js_txt["sum"]
        list_song = js_txt["list_songs"]
        align = js_txt["align"]
        color = js_txt["color_song"]
        size_txt = js_txt["size_txt"]
        path_font_song = js_txt["path_font_song"]

        if len(list_song) != sum:
            print("Data is wrong")
            result["content"] = "Data is wrong"
            return result

    except Exception as error:
        print(error)
        result["content"] = error
        return result

    if align not in ["center", "left", "right"]:
        result["content"] = "align must be in [center, left, right]"
        return result

    if align == "center":
        align = "right"

    # Get color to draw text
    color = _get_color(color, 255)
    if color is False:
        result["content"] = "color format is not right"
        return result

    # Get font song
    font_song = _get_font(path_font_song)

    if font_song is False:
        print("Font file or folder not found!")
        result["content"] = "Font file or folder not found or format not True!"
        return result

    if debug:
        print(text_region)

    _list_col_right = []
    _list_col_left = []

    text_region = list(text_region)
    # Add offset height for text region
    text_region[1] = int(text_region[1]) + WIDTH_LINE

    im = Image.open(im_ob).convert('RGBA')
    width_img, height_img = im.size

    new_size = _get_new_size(width_img, height_img)
    if new_size is False:
        pass
    else:
        width_img, height_img = new_size
        new_size = (1280, 720)

        im = im.resize(new_size)

    # Check position of left
    _location_text = 'left'
    if text_region[0] > W/3:
        _location_text = 'right'

    # make a blank image for the text, initialized to transparent text color
    txt = Image.new('RGBA', im.size, (255, 255, 255, 0))

    _fnt_song = ImageFont.truetype(font_song, size_txt)
    _d_song = ImageDraw.Draw(txt)
    _width_text, _height_text = _d_song.textsize('test', font=_fnt_song)
    del _d_song, txt

    space_line = int(0.6 * _height_text)

    txt = Image.new('RGBA', im.size, (255, 255, 255, 0))

    # Adjust text region
    try:
        title = js_txt["title"]
        font_title = js_txt["path_font_title"]
        size_title = js_txt["size_title"]
        _color_title = js_txt["color_title"]
        color_title = _get_color(_color_title, 255)
        if color_title is False:
            result["content"] = f"{color_title} format is not True"
            return result

        title_region = text_region
        # make a blank image for the text, initialized to transparent text color
        txt = Image.new('RGBA', im.size, (255, 255, 255, 0))

        # Get param of title
        fnt = ImageFont.truetype(font_title, size_title)
        # get a drawing context
        d = ImageDraw.Draw(txt)
        width_title, height_title = d.textsize(title, font=fnt, spacing=2*space_line)
        _width_text_region = text_region[2] - text_region[0]
        width = _width_center(width_text=width_title, width_img=_width_text_region)

        while width is False:
            size_title -= 1
            # get a font
            fnt = ImageFont.truetype(font_title, size_title)
            width_title, height_title = d.textsize(title, font=fnt, spacing=space_line)
            width = _width_center(width_text=width_title, width_img=_width_text_region)

        height_offset_song = int(height_title + 6 * WIDTH_LINE)

    except:
        title = False
        height_offset_song = 2 * WIDTH_LINE

    # Adjust parameter text region
    text_region = list(text_region)
    text_region[1] = int(text_region[1]) + height_offset_song

    # Draw song into image
    # Create new param
    height_song_top = int(text_region[1])  # The coordinate height song top
    height_song_bottom = int(text_region[3])  # The coordinate height song bottom

    fnt = ImageFont.truetype(font_song, size_txt)
    # get a drawing content
    d = ImageDraw.Draw(txt)

    song_str = {}
    stop = False
    # The song number
    j = 0
    sum_song_one_col = 0
    count_img = 0
    min_offset = (text_region[2] - text_region[0]) // 2
    _list_song = list_song.copy()
    _tmp_index = 0

    for _index, song in enumerate(_list_song):
        _song_str = f"{_get_number(_index)}. {song['name']}\n"
        width_text, height_text = d.textsize(_song_str, font=fnt, spacing=space_line)
        if width_text > int((text_region[2] - text_region[0]) / 2) + OFFSET_TEXT - 60:
            list_song.pop(_tmp_index)
            _tmp_index -= 1
        else:
            min_offset = (text_region[2] - text_region[0]) // 2 - (width_text + 60) \
                if min_offset > (text_region[2] - text_region[0]) // 2 - (width_text + 60) else min_offset
        _tmp_index += 1

    # The list coordinate of width song fl collum
    if min_offset > 0:
        left_col = text_region[0] + min_offset // 2
    else:
        if _location_text == 'right':
            left_col = text_region[0] + min_offset - 60
            text_region[0] = left_col
        else:
            left_col = text_region[0]

    if min_offset > 0:
        right_col = int((text_region[2] + text_region[0] - min_offset) / 2) + 20

    else:
        if _location_text == "right":
            right_col = int((text_region[0] + text_region[2]) // 2)
            # Align title to center
            _width_text_region = text_region[2] - text_region[0]
        else:
            right_col = int((text_region[0] + text_region[2]) // 2 - min_offset) + 20
            text_region[2] += abs(min_offset)
            # Align title to center
            _width_text_region = text_region[2] - text_region[0]

    # if text_region[2] > 2 * W / 3:
    #     # The list coordinate of width song fl collum
    #     if min_offset > 0:
    #         left_col = text_region[0] + min_offset // 2
    #     else:
    #         left_col = text_region[0] - min_offset
    #
    #     if min_offset > 0:
    #         right_col = int((text_region[2] + text_region[0] - min_offset) / 2) + 20
    #     else:
    #         right_col = int((text_region[0] + text_region[2]) // 2) + 20
    #         text_region[0] -= abs(min_offset)
    #         # Align title to center
    #         _width_text_region = text_region[2] - text_region[0]

    width_song = [left_col, right_col]

    if debug:
        print(list_song)

    # To know col_status is left or right
    col_status = "left"
    # To save list song follow collum
    _count_col_right = 0
    song_str[f'img_{count_img}'] = []
    _max_width_col_left = 0

    while j < len(list_song):  # Not finish list

        # clear height before to use
        height_text = 0

        song_str[f'list_song_{count_img}_{col_status}'] = ''

        while (height_song_bottom - height_song_top - height_text) > 0:  # Check end of the height image
            # Calculator width of image count_img
            song_str[f'img_{count_img}'].append(list_song[j]['name'])
            song_str[f'list_song_{count_img}_{col_status}'] += f"{_get_number(j)}. {list_song[j]['name']}\n"
            width_text, height_text = d.textsize(f"{song_str[f'list_song_{count_img}_{col_status}']}\n",
                                                 font=fnt, spacing=space_line)
            if col_status == "left":
                _max_width_col_left = _max_width_col_left if _max_width_col_left > width_text else width_text
                _count_col_right = 0
            # max_width_ = width_text if width_text > max_width else max_width
            else:
                _count_col_right += 1
            if stop is False:
                sum_song_one_col += 1
            j += 1
            if j >= len(list_song):
                break

        if stop is False:
            stop = True

        if col_status == "left":
            col_status = "right"
        else:
            col_status = "left"
            count_img += 1
            if count_img == int(len(list_song) // (sum_song_one_col * 2)):
                break

            song_str[f'img_{count_img}'] = []

    _range_width_empty = right_col - _max_width_col_left

    if debug:
        print(f"width_song is {width_song}")
        print(f"song_str is {song_str}")

    if count_img == 1:
        if _count_col_right != sum_song_one_col:
            result["content"] = "Song not enough for draw two collum"
            return result
    # Draw song into the picture
    warring_status = False
    for img in range(count_img):
        txt = Image.new('RGBA', im.size, (255, 255, 255, 0))
        fnt = ImageFont.truetype(font_song, size_txt)

        # get a drawing content
        d = ImageDraw.Draw(txt)
        d.multiline_text((width_song[0], height_song_top),
                         text=song_str[f'list_song_{img}_left'], font=fnt, fill=color,
                         align=align, spacing=space_line)
        d.multiline_text((width_song[1], height_song_top),
                         text=song_str[f'list_song_{img}_right'], font=fnt, fill=color,
                         align="left", spacing=space_line)

        if title is False:
            pass
        else:
            width = _width_center(width_text=width_title, width_img=_width_text_region)
            width += text_region[0]
            if debug:
                print("width is ", width)
            d = ImageDraw.Draw(txt)
            fnt = ImageFont.truetype(font_title, size_title)

            # Set height in top off image
            height = title_region[1] if title_region[1] != 0 else title_region[1] + 20
            # Draw underline and tile:
            coordinate_txt = (width, height)

            d.multiline_text(coordinate_txt, text=title, font=fnt,
                             fill=color_title, align='center')
        if debug:
            txt.show()

        _im_tmp = im.copy()
        out = Image.alpha_composite(_im_tmp, txt)
        if debug:
            out.show()

        time = datetime.now()
        current_time = time.strftime("%H:%M:%S:%f")
        current_date = time.date()

        path_new = f"{path_output}/{current_date}_{current_time}.png"

        try:
            out.save(path_new)
        except Exception as error:
            print(error)
            warring_status = True
            result["content"] += f"{error}\n"
            continue
        _tmp_dict = {
            "path_img": path_new,
            "list_songs": song_str[f'img_{img}']
        }
        result["data"].append(_tmp_dict)

    if warring_status:
        result["status"] = "warring"
    else:
        if len(result["data"]) == 0:
            result["status"] = "error"
            result["content"] = "song not enough for draw two collum"
        else:
            result["status"] = "success"

    # del time, current_time, current_date, fnt, im

    return result


def draw_one_col_singer(im_ob, text_region, path_output, js_txt, debug=False):
    """
Detail : This function to draw text into the picture
    :param im_ob:
    :param text_region:
    :param path_output:
    :param js_txt:
    :param debug:
    :return:
    """

    # To create new variable
    result = dict()
    result["status"] = "error"
    result["content"] = ''
    result["data"] = []
    result["image_false"] = ''

    # check conditional
    if os.path.isdir(path_output) is False:
        print(f"Cannot find {path_output}")
        result["content"] = f"Cannot find {path_output}"
        return result

    if len(text_region) != 4:
        print("Text region format not true")
        result["content"] = "Text region format not true"
        return result
    else:
        title_region = text_region

    if js_txt is None:
        print("No json file import")
        result["content"] = "No json file import"
        return result

    try:
        sum = js_txt["sum"]
        list_song = js_txt["list_songs"]
        list_singer = js_txt["list_singer"]
        size_txt = js_txt["size_txt"]
        path_font_song = js_txt["path_font_song"]
        path_font_singer = js_txt["path_font_singer"]

        if len(list_song) != sum:
            print("Data list song is wrong")
            result["content"] = "Data list songs is wrong"
            return result
        if len(list_singer) != sum:
            print("Data singer is wrong")
            result["content"] = "Data list singer is wrong"
            return result

    except Exception as error:
        print(error)
        result["content"] = error
        return result

    try:
        mode = js_txt["mode"]
        if mode not in ["line", "no_line", "singer"]:
            print(f"{js_txt['mode']} must have line or no_line or singer")
            result["content"] = f"{js_txt['mode']} must have line or no_line"
            return result
    except:
        mode = "singer"


    try:
        color_song = js_txt["color_song"]
        color_singer = js_txt["color_singer"]

    except Exception as error:
        result["content"] = error
        return result

    # Get color to draw text
    color_song = _get_color(color_song, 255)

    color_singer = _get_color(color_singer, 200)
    if color_singer is False:
        result["content"] = "color format is not right"
        return result

    if color_song is False:
        result["content"] = "color format is not right"
        return result

    # Get font song
    font_song = _get_font(path_font_song)
    font_singer = _get_font(path_font_singer)

    if font_song is False or font_singer is False:
        print("Font file or folder not found!")
        result["content"] = "Font file not found or format not True!"
        return result

    if debug:
        print(text_region)

    im = Image.open(im_ob).convert('RGBA')
    width_img, height_img = im.size

    new_size = _get_new_size(width_img, height_img)

    if new_size is False:
        pass
    else:
        width_img, height_img = new_size
        im = im.resize((W, H))

    # Adjust text region
    try:
        title = js_txt["title"]
        font_title = js_txt["path_font_title"]
        size_title = js_txt["size_title"]
        _color_title = js_txt["color_title"]
        color_title = _get_color(_color_title, 255)
        if color_title is False:
            result["content"] = f"{color_title} format is not True"
            return result

        # make a blank image for the text, initialized to transparent text color
        txt = Image.new('RGBA', im.size, (255, 255, 255, 0))

        # Get param of title
        fnt = ImageFont.truetype(font_title, size_title)
        # get a drawing context
        d = ImageDraw.Draw(txt)
        width_title, height_title = d.textsize(title, font=fnt, spacing=2*HEIGHT_OFFSET)
        _width_text_region = text_region[2] - text_region[0]
        width = _width_center(width_text=width_title, width_img=_width_text_region)

        while width is False:

            size_title -= 1
            # get a font
            fnt = ImageFont.truetype(font_title, size_title)
            width_title, height_title = d.textsize(title, font=fnt, spacing=2*HEIGHT_OFFSET)
            width = _width_center(width_text=width_title, width_img=_width_text_region)

        height_offset_song = int(height_title + 6 * WIDTH_LINE)

    except:
        title = False
        height_offset_song = 2 * WIDTH_LINE

    # Adjust parameter text region
    text_region = list(text_region)
    text_region[1] = int(text_region[1]) + height_offset_song + 20

    # make a blank image for the text, initialized to transparent text color
    txt = Image.new('RGBA', im.size, (255, 255, 255, 0))

    _fnt_song = ImageFont.truetype(font_song, size_txt)
    _d_song = ImageDraw.Draw(txt)
    _width_text, _height_text = _d_song.textsize('test', font=_fnt_song)
    del _d_song, txt

    space_line = int(1.5 * _height_text)
    _height_singer_ = _height_text
    _size_singer = size_txt

    if debug:
        print(space_line)

    txt = Image.new('RGBA', im.size, (255, 255, 255, 0))
    d = ImageDraw.Draw(txt)

    while _height_singer_ > ((4 * _height_text) / 5):
        _size_singer -= 1
        fnt = ImageFont.truetype(font_singer, _size_singer)
        # get a drawing content
        _width_singer_, _height_singer_ = d.textsize("test", font=fnt)
    del txt, d

    txt = Image.new('RGBA', im.size, (255, 255, 255, 0))
    d = ImageDraw.Draw(txt)

    fnt_singer = ImageFont.truetype(font_singer, _size_singer)
    fnt_song = ImageFont.truetype(font_song, size_txt)
    _range_txt = text_region[2] - text_region[0] - EDGE_OFFSET

    if debug:
        print(f"size of singer is {_size_singer}")

    _list_song = list_song.copy()
    _list_singer = list_singer.copy()
    _tmp_index = 0
    _max_width = 0

    for _index, song in enumerate(_list_song):
        # Get string of song and define width and height of song
        _song_str = f"{_get_number(_index)}. {song['name']}\n"
        _width_song, _height_song = d.textsize(_song_str, font=fnt_song)

        # Check mode, with one of mode will be set mode follow config
        if mode == "line":
            _singer_str = f"{_list_singer[_index]['name']}"
            _width_singer, _height_singer = d.textsize(_singer_str, font=fnt_singer)

            # check conditional to remove element
            if _width_song + _width_singer + 5 * WIDTH_LINE > _range_txt:
                list_singer.pop(_tmp_index)
                list_song.pop(_tmp_index)
                _tmp_index -= 1

        elif mode == "no_line":
            _singer_str = f"{_list_singer[_index]['name']}"
            _height_singer, _width_singer = d.textsize(_singer_str, font=fnt_singer)

            # check conditional to remove element
            if _width_song + _width_singer + 3 * WIDTH_LINE > _range_txt:
                list_singer.pop(_tmp_index)
                list_song.pop(_tmp_index)
                _tmp_index -= 1
        else:
            _singer_str = f"- {_list_singer[_index]['name']}"
            _height_singer, _width_singer = d.textsize(_singer_str, font=fnt_singer)
            _max_width = max(_width_singer, _width_song)

            # check conditional to remove element
            if _max_width > _range_txt:
                list_singer.pop(_tmp_index)
                list_song.pop(_tmp_index)
                _tmp_index -= 1
        _tmp_index += 1

    # Draw song into image
    # Create new param
    max_width = 0
    height_song_top = int(text_region[1])
    height_song_bottom = int(text_region[3])
    _with_song = int((text_region[2] - text_region[0] - _max_width) / 2) + text_region[0]
    width_song = _with_song

    if debug:
        print(width_song)

    fnt = ImageFont.truetype(font_song, size_txt)
    # get a drawing content
    d = ImageDraw.Draw(txt)

    height_text = 0
    song_str = dict()
    singer_str = dict()

    # The song number
    j = 0
    _count_song_one_collum = 0
    _check_count_song = False
    _count_img = 0

    while j < len(list_song):  # Not finish list

        # To save list song follow collum
        song_str[f'img_{_count_img}'] = []
        song_str[f'list_song_{_count_img}'] = ''
        singer_str[f'list_singer_{_count_img}'] = ''

        while (height_song_bottom - height_song_top - height_text) > 0:  # Check end of the height image
            # Calculator width of collum i
            song_str[f'img_{_count_img}'].append(list_song[j]['name'])
            song_str[f'list_song_{_count_img}'] += f"{_get_number(j)}. {list_song[j]['name']}\n"
            if mode == "singer":
                singer_str[f'list_singer_{_count_img}'] += f"  - {list_singer[j]['name']}\n"
            else:
                singer_str[f'list_singer_{_count_img}'] += f"{list_singer[j]['name']}\n"

            width_text, height_text = d.textsize(song_str[f'list_song_{_count_img}'] + "\n\n",
                                                 font=fnt, spacing=space_line)

            max_width = width_text if width_text > max_width else max_width

            if not _check_count_song:
                _count_song_one_collum += 1

            j += 1
            if j >= len(list_song):
                break

        if not _check_count_song:
            _check_count_song = True

        # auto ad image
        _count_img += 1

        if _count_img == len(list_song) // _count_song_one_collum:
            break

        height_text = 0

    if debug:
        print(width_song)

    # Draw singer
    _offset_line = space_line - _height_singer_

    if debug:
        print(f"the number of song in one page {j}")
        print(f"mode is {mode}")

    # To check warring status
    warring_status = False

    for img in range(_count_img):
        _tmp_img = im.copy()
        txt = Image.new('RGBA', im.size, (255, 255, 255, 0))
        fnt = ImageFont.truetype(font_singer, _size_singer)
        d_tmp = ImageDraw.Draw(txt)
        _width_tmp, _height_tmp = d_tmp.textsize(singer_str[f'list_singer_{img}'], font=fnt)

        d = ImageDraw.Draw(txt)

        if mode != "singer":

            if (text_region[2] - text_region[0]) > (_width_tmp + max_width):
                if mode == "no_line":
                    # Draw with no line
                    _width_singer = width_song - _width_tmp + 5

                    if debug:
                        print(_width_singer)
                        print(_width_tmp)
                    spacing = _offset_line + _height_text

                    d.multiline_text((_width_singer, height_song_top + _height_text + int(_offset_line / 2)),
                                     text=singer_str[f'list_singer_{img}'], font=fnt,
                                     fill=color_singer, align="right", spacing=spacing)
                if mode == "line":
                    # Draw with line
                    _width_singer = width_song - _width_tmp - WIDTH_LINE * 5
                    if _width_singer < 0:
                        print("text too long")
                        return False

                    if debug:
                        print(_width_singer)
                        print(_width_tmp)

                    # To calculator spacing for singer
                    spacing = _offset_line + _height_text

                    # To calculator height_text of song
                    fnt_song = ImageFont.truetype(font_singer, size_txt)
                    width_text, height_text = d.textsize(song_str[f'list_song_{img}'] + "\n",
                                                         font=fnt_song, spacing=space_line)

                    d.multiline_text((_width_singer, height_song_top + _height_text + int(_offset_line / 2)),
                                     text=singer_str[f'list_singer_{img}'],
                                     font=fnt, fill=color_singer, align="right", spacing=spacing)

                    # calculator coordinate of line
                    line_xy_1 = (width_song - WIDTH_LINE * 2 + LONG_WIDTH,
                                 height_song_top - int(0.6 * spacing))
                    line_xy_2 = (width_song - WIDTH_LINE * 2,
                                 height_song_top - int(0.6 * spacing))
                    # line_xy_3 = (width_song - WIDTH_LINE * 2,
                    #              height_text - spacing)
                    # line_xy_4 = (width_song - WIDTH_LINE * 2 - 1.4 * LONG_WIDTH,
                    #              height_text - spacing)
                    line_xy_3 = (width_song - WIDTH_LINE * 2,
                                 height_text + height_song_top - space_line)
                    line_xy_4 = (width_song - WIDTH_LINE * 2 - 1.4 * LONG_WIDTH,
                                 height_text + height_song_top - space_line)

                    d_line = ImageDraw.Draw(txt)
                    d_line.line([line_xy_1, line_xy_2, line_xy_3, line_xy_4],
                                fill=(255, 250, 248), width=2)
                    if debug:
                        txt.show()
            else:
                print("text too long")
                return False

        else:

            # check condition leng of width text
            if (text_region[2] - text_region[0]) < (_width_tmp + max_width):
                print("text too long")
                return False

            # Draw with one collum
            spacing = _offset_line + _height_text
            width_song = text_region[0] + int((text_region[2] - text_region[0] - _width_tmp) / 2)

            if debug:
                print(width_song)

            d.multiline_text((width_song + 5, height_song_top + _height_text + int(_offset_line / 2)),
                             text=singer_str[f'list_singer_{img}'],
                             font=fnt, fill=color_singer, align="left", spacing=spacing)

        # Draw song into the picture
        fnt = ImageFont.truetype(font_song, size_txt)
        # get a drawing content
        d = ImageDraw.Draw(txt)
        d.multiline_text((width_song, height_song_top),
                         text=song_str[f'list_song_{img}'],
                         font=fnt, fill=color_song,
                         align='left', spacing=space_line)

        if title is False:
            pass
        else:
            width = _width_center(width_text=width_title, width_img=_width_text_region)
            width += text_region[0]
            d = ImageDraw.Draw(txt)
            fnt = ImageFont.truetype(font_title, size_title)
            width_text, height_text = d.textsize(title, font=fnt)

            # Set height in top off image
            height = title_region[1] + 10 if title_region[0] == 0 else title_region[0]

            # Draw underline and tile:
            coordinate_txt = (width, height)

            # _draw = ImageDraw.Draw(txt)
            #
            # _draw.line((width + WIDTH_OFFSET, height + HEIGHT_OFFSET + height_text,
            #             width + width_text - WIDTH_OFFSET, height + HEIGHT_OFFSET + height_text),
            #            width=5, fill=(255, 255, 255, 255))
            d.multiline_text(coordinate_txt, text=title, font=fnt,
                             fill=color_title, align='center', spacing=2*HEIGHT_OFFSET)
        if debug:
            txt.show()

        out = Image.alpha_composite(_tmp_img, txt)
        if debug:
            out.show()

        time = datetime.now()
        current_time = time.strftime("%H:%M:%S:%f")
        current_date = time.date()

        path_new = f"{path_output}/{current_date}_{current_time}.png"

        try:
            out.save(path_new)
        except Exception as error:
            print(error)
            warring_status = True
            result["content"] += f"{error}\n"
            continue
        _tmp_dict = {
            "path_img": path_new,
            "list_songs": song_str[f'img_{img}']
        }
        result["data"].append(_tmp_dict)

    if warring_status:
        result["status"] = "warring"
    else:
        if len(result["data"]) == 0:
            result["status"] = "error"
            result["content"] = "song not enough for draw two collum"
        else:
            result["status"] = "success"

    # del out, time, current_time, current_date, fnt, im

    return result


def draw_double_col_2_side(im_ob, text_region, path_output, js_txt, debug=False):
    """
 Detail: This to draw in image with style no singer and one collum
     :param im_ob:
     :param text_region:
     :param path_output:
     :param js_txt:
     :param debug:
     :return:
     """

    # To create new variable
    result = dict()
    result["status"] = "error"
    result["content"] = ''
    result["data"] = []
    result["image_false"] = ''

    if len(text_region) != 2:
        print(f"{text_region} format not True")
        result["content"] = f"{text_region} format not True"
        return result

    for text_rg in text_region:
        if len(text_rg) != 4:
            print("Text region format not true")
            result["content"] = f"Text region {text_rg} format not True"
            return result

    # check conditional
    if os.path.isdir(path_output) is False:
        print(f"Cannot find {path_output}")
        result["content"] = f"Cannot find {path_output}"
        return result

    if js_txt is None:
        print("No json file import")
        result["content"] = "No json file import"
        return result

    try:
        sum = js_txt["sum"]
        list_song = js_txt["list_songs"]
        color = js_txt["color_song"]
        size_txt = js_txt["size_txt"]
        path_font_song = js_txt["path_font_song"]

        if len(list_song) != sum:
            print("Data is wrong")
            result["content"] = "Data is wrong"
            return result
    except Exception as error:
        print(error)
        result["content"] = error
        return result

    # Get color to draw text
    color = _get_color(color, 255)

    if color is False:
        result["content"] = "color format is not right"
        return result

    # Get font song
    font_song = _get_font(path_font_song)

    if font_song is False:
        print("Font file or folder not found!")
        result["content"] = "Font file or folder not found or format not True!"
        return result

    if debug:
        print(text_region)

    im = Image.open(im_ob).convert('RGBA')
    width_img, height_img = im.size

    new_size = _get_new_size(width_img, height_img)
    if new_size is False:
        pass
    else:
        width_img, height_img = new_size
        im = im.resize(new_size)

    # Adjust text region
    try:
        title = js_txt["title"]
        font_title = js_txt["path_font_title"]
        size_title = js_txt["size_title"]
        _color_title = js_txt["color_title"]
        color_title = _get_color(_color_title, 255)
        if color_title is False:
            result["content"] = f"{color_title} format is not True"
            return result

        # make a blank image for the text, initialized to transparent text color
        txt = Image.new('RGBA', im.size, (255, 255, 255, 0))

        # Get param of title
        fnt = ImageFont.truetype(font_title, size_title)

        # get a drawing context
        d = ImageDraw.Draw(txt)
        width_title, height_title = d.textsize(title, font=fnt, spacing=2*HEIGHT_OFFSET)
        width = _width_center(width_text=width_title, width_img=width_img)

        # Fix size text with into picture
        height_offset_song = 20

        # Auto resize of title if size of title too big
        while width is False:
            size_title -= 1
            # get a font
            fnt = ImageFont.truetype(font_title, size_title)
            width_title, height_title = d.textsize(title, font=fnt, spacing=2*HEIGHT_OFFSET)
            width = _width_center(width_text=width_title, width_img=width_img)
            height_offset_song = int(2 * HEIGHT_OFF_SONG + height_title * 1.5)
        _max_region_text = max(abs(text_region[0][2] - text_region[0][0]),
                               abs(text_region[1][2] - text_region[1][0]))
        if width_title > width_img - 2 * _max_region_text:
            height_offset_song = int(2 * HEIGHT_OFF_SONG + height_title * 1.5)
    except:
        title = False
        height_offset_song = 20

    _max_region_text = OFFSET_TEXT + max(abs(text_region[0][2] - text_region[0][0]),
                                         abs(text_region[1][2] - text_region[1][0]))

    for index in range(len(text_region)):
        text_region[index] = list(text_region[index])
        text_region[index][1] += height_offset_song
        text_region[index][3] -= 20

    _list_col_right = []
    _list_col_left = []

    # make a blank image for the text, initialized to transparent text color
    txt = Image.new('RGBA', im.size, (255, 255, 255, 0))

    _fnt_song = ImageFont.truetype(font_song, size_txt)
    _d_song = ImageDraw.Draw(txt)
    _width_text, _height_text = _d_song.textsize('test', font=_fnt_song)
    del _d_song, txt

    space_line = int(0.6 * _height_text)

    txt = Image.new('RGBA', im.size, (255, 255, 255, 0))

    # Draw song into image
    # Create new param
    height_song_top = int(text_region[0][1])  # The coordinate height song top
    height_song_bottom = int(text_region[0][3])  # The coordinate height song bottom

    fnt = ImageFont.truetype(font_song, size_txt)
    # get a drawing content
    d = ImageDraw.Draw(txt)

    song_str = dict()
    _size_tmp = dict()
    stop = False
    # The song number
    j = 0
    sum_song_one_col = 0
    count_img = 0
    _list_song = list_song.copy()
    _tmp_index = 0

    for _index, song in enumerate(_list_song):
        _song_str = f"{_get_number(_index)}. {song['name']}\n"
        width_text, height_text = d.textsize(_song_str, font=fnt, spacing=space_line)
        if width_text > _max_region_text:
            list_song.pop(_tmp_index)
            _tmp_index -= 1
        _tmp_index += 1

    if debug:
        print(list_song)

    # To know col_status is left or right
    col_status = "left"
    _count_col_right = 0
    # To save list song follow collum
    song_str[f'img_{count_img}'] = []
    _max_width_col_left = 0

    while j < len(list_song):  # Not finish list

        # clear height before to use
        height_text = 0

        song_str[f'list_song_{count_img}_{col_status}'] = ''

        while (height_song_bottom - height_song_top - height_text) > 0:  # Check end of the height image
            # Calculator width of image count_img
            song_str[f'img_{count_img}'].append(list_song[j]['name'])
            song_str[f'list_song_{count_img}_{col_status}'] += f"{_get_number(j)}. {list_song[j]['name']}\n"
            width_text, height_text = d.textsize(f"{song_str[f'list_song_{count_img}_{col_status}']}\n",
                                                 font=fnt, spacing=space_line)
            if col_status == "left":
                _count_col_right = 0
                _max_width_col_left = _max_width_col_left if _max_width_col_left > width_text else width_text
            else:
                _count_col_right += 1

            # max_width_ = width_text if width_text > max_width else max_width
            if stop is False:
                sum_song_one_col += 1
            j += 1
            if j >= len(list_song):
                break

        if stop is False:
            stop = True

        if col_status == "left":
            col_status = "right"
        else:
            col_status = "left"
            _size_tmp[f"width_{count_img}"] = width_text
            count_img += 1
            if count_img == int(len(list_song) // (sum_song_one_col * 2)):
                break

            song_str[f'img_{count_img}'] = []

    if debug:
        print(f"song_str is {song_str}")

    if count_img == 1:
        if _count_col_right != sum_song_one_col:
            result["content"] = "Song not enough for draw two collum"
            return result

    # Draw song into the picture
    warring_status = False
    for img in range(count_img):
        txt = Image.new('RGBA', im.size, (255, 255, 255, 0))
        fnt = ImageFont.truetype(font_song, size_txt)

        # get a drawing content
        d = ImageDraw.Draw(txt)
        d.multiline_text((text_region[0][0], height_song_top),
                         text=song_str[f'list_song_{img}_left'], font=fnt, fill=color,
                         align="left", spacing=space_line)
        _width_right = text_region[1][2] - _size_tmp[f"width_{img}"]
        d.multiline_text((_width_right, height_song_top),
                         text=song_str[f'list_song_{img}_right'], font=fnt, fill=color,
                         align="right", spacing=space_line)

        if title is False:
            pass
        else:
            # width = _width_center(width_text=width_title, width_img=width_img)
            d = ImageDraw.Draw(txt)
            fnt = ImageFont.truetype(font_title, size_title)
            width_text, height_text = d.textsize(title, font=fnt)

            # Set height in top off image
            height = 30

            # Draw underline and tile:
            coordinate_txt = (width, height)

            # _draw = ImageDraw.Draw(txt)
            #
            # _draw.line((width + WIDTH_OFFSET, height + HEIGHT_OFFSET + height_text,
            #             width + width_text - WIDTH_OFFSET, height + HEIGHT_OFFSET + height_text),
            #            width=5, fill=(255, 255, 255, 255))
            d.multiline_text(coordinate_txt, text=title, font=fnt, fill=color_title,
                             align='center', spacing=2*HEIGHT_OFFSET)
        if debug:
            txt.show()

        _im_tmp = im.copy()
        out = Image.alpha_composite(_im_tmp, txt)
        if debug:
            out.show()

        time = datetime.now()
        current_time = time.strftime("%H:%M:%S:%f")
        current_date = time.date()

        path_new = f"{path_output}/{current_date}_{current_time}.png"

        try:
            out.save(path_new)
        except Exception as error:
            print(error)
            warring_status = True
            result["content"] += f"{error}\n"
            continue

        _tmp_dict = {
            "path_img": path_new,
            "list_songs": song_str[f'img_{img}']
        }
        result["data"].append(_tmp_dict)

    if warring_status:
        result["status"] = "warring"
    else:
        if len(result["data"]) == 0:
            result["status"] = "error"
            result["content"] = "song not enough for draw two collum"
        else:
            result["status"] = "success"

    return result


if __name__ == "__main__":

    im_ob = "./develop_env/object/pexels-tuáº¥n-kiá»t-jr-1382726.jpg"

    path_out = "./develop_env/output"
    text_region_1 = [(10, 0, 300, 720), (700, 0, 1070, 720)]
    text_region = [730, 0, 1270, 720]

    try:
        with open('./develop_env/data/list_song.json') as json_file:
            data = json.load(json_file)
    except ValueError as error:
        print(error)

    result = draw_one_col_singer(im_ob, text_region, path_output=path_out, js_txt=data, debug=True)
    print(result)

    # try:
    #     with open('./develop_env/data/list_song.json') as json_file:
    #         data = json.load(json_file)
    # except ValueError as error:
    #     print(error)
    # result = draw_double_col_2_side(im_ob, text_region_1, path_output=path_out, js_txt=data, debug=True)
    # print(result)

    try:
        with open('./develop_env/data/list_song.json') as json_file:
            data = json.load(json_file)
    except ValueError as error:
        print(error)

    result = draw_one_col_no_singer(im_ob, text_region, path_output=path_out, js_txt=data, debug=True)

    try:
        with open('./develop_env/data/list_song.json') as json_file:
            data = json.load(json_file)
    except ValueError as error:
        print(error)

    result = draw_double_col(im_ob, text_region, path_output=path_out, js_txt=data, debug=True)
    print(result)

    # im = Image.open(path)
    # im.show()
