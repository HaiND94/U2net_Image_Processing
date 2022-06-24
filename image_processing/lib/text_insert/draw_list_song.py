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


# Height center alignment
def _height_center(height_text, height_img):
    if height_text > height_img:
        return False

    return int((height_img - height_text) / 2) if (height_img - height_text) >= 0 else False


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


# Set tile region
def _title_region(text_region):
    """

    :param text_region:
    :return:
    """
    if len(text_region) != 4:
        return False
    title_region = []
    title_region.append(text_region[0])
    title_region.append(text_region[1])
    title_region.append(text_region[2])
    title_region.append(int(text_region[3] / 3 - 20))

    return title_region


# Set song region
def _song_region(text_region, title_region):
    """

    :param text_region:
    :param title_region:
    :return:
    """
    if len(text_region) != 4 or len(title_region) != 4:
        return False

    song_region = []

    song_region.append(text_region[0])
    song_region.append(title_region[3])
    song_region.append(text_region[2])
    song_region.append(text_region[3])

    return song_region


# Draw title
def _draw_title(title, size_title, font_1, font_2, color_1, color_2, title_region, im, debug=False):
    """
    Detail: Draw title
    :param title:
    :param title_size:
    :param font_1:
    :param font_2:
    :param color_1:
    :param color_2:
    :return:
    """

    if not os.path.isfile(font_1):
        print(f"{font_1} should be not found")
        return False

    if not os.path.isfile(font_2):
        print(f"{font_2} should be not found")
        return False

    titles = []
    _titles = title.split(" ")
    _status_same = False
    list_color = [color_1, color_2]

    if len(_titles) == 1:
        titles = _titles.copy()
        pass

    elif len(_titles) % 2 == 0:
        _status_same = True
        _word_one_line = int(len(_titles) // 2)
        titles.append('')
        titles.append('')

        # Split to two string
        for idx in range(_word_one_line):
            titles[0] += f"{_titles[idx]} "
            titles[1] += f"{_titles[_word_one_line + idx]} "

        # Remove space digit in the and of the line
        tmp = titles[0]
        titles[0] = tmp[:-1]
        tmp = titles[1]
        titles[1] = tmp[:-1]

    else:
        _status_same = False
        titles.append('')
        titles.append('')

        # Split to two string
        for idx in range(len(_titles)-1):
            titles[0] += f"{_titles[idx]} "

        titles[1] += _titles[-1]
        # Remove space digit in the and of the line
        tmp = titles[0]
        titles[0] = tmp[:-1]

    if len(titles) == 1:
        # make a blank image for the text, initialized to transparent text color
        txt = Image.new('RGBA', im.size, (255, 255, 255, 0))

        # Get param of title
        fnt = ImageFont.truetype(font_1, size_title)

        # get a drawing context
        d = ImageDraw.Draw(txt)
        width_title, height_title = d.textsize(title, font=fnt, spacing=HEIGHT_OFFSET)
        _width_text_region = title_region[2] - title_region[0]
        width = _width_center(width_text=width_title, width_img=_width_text_region)

        # # To expand text region
        # if width is False:
        #     _title_change_status = True
        #     _width_text_region += OFFSET_TEXT
        #     width = _width_center(width_text=width_title, width_img=_width_text_region)

        # If width is False, auto resize size of title
        while width is False:
            size_title -= 1
            # Get a font
            fnt = ImageFont.truetype(font_1, size_title)
            width_title, height_title = d.textsize(title, font=fnt, spacing=HEIGHT_OFFSET)
            width = _width_center(width_text=width_title, width_img=_width_text_region)

        # Caculator coordinate for title
        _height_im = title_region[3] - title_region[1]
        height = title_region[1] + _height_center(height_title, _height_im)

        width += title_region[0]

        # make a blank image for the text, initialized to transparent text color
        txt = Image.new('RGBA', im.size, (255, 255, 255, 0))
        fnt = ImageFont.truetype(font_1, size_title)

        # get a drawing context
        d = ImageDraw.Draw(txt)
        coordinate_txt = (width, height)
        d.multiline_text(coordinate_txt, text=title, font=fnt, fill=color_1, align='center')
        if debug:
            txt.show()

        return txt

    elif len(titles) == 2:
        list_font = [font_1, font_2]
        if _status_same:

            # make a blank image for the text, initialized to transparent text color
            tmp = dict()
            height_offset = 0

            for idx, title in enumerate(titles):
                txt = Image.new('RGBA', im.size, (255, 255, 255, 0))
                # Get param of title
                fnt = ImageFont.truetype(list_font[idx], size_title)
                # get a drawing context
                d = ImageDraw.Draw(txt)
                width_title, height_title = d.textsize(title, font=fnt, spacing=HEIGHT_OFFSET)

                if idx == 0:
                    _width_text_region = title_region[2] - title_region[0]
                else:
                    _width_text_region = title_region[2] - title_region[0]

                width = _width_center(width_text=width_title, width_img=_width_text_region)

                # # To expand text region
                # if width is False:
                #     _title_change_status = True
                #     _width_text_region += OFFSET_TEXT
                #     width = _width_center(width_text=width_title, width_img=_width_text_region)

                # If width is False, auto resize size of title
                while width is False:
                    size_title -= 1
                    # Get a font
                    fnt = ImageFont.truetype(list_font[idx], size_title)
                    width_title, height_title = d.textsize(title, font=fnt, spacing=HEIGHT_OFFSET)
                    width = _width_center(width_text=width_title, width_img=_width_text_region)
                if idx == 0:
                    _height_im = title_region[3] - title_region[1]
                    height = title_region[1] + _height_center(2 * height_title, _height_im)
                    height_offset = height + height_title
                else:
                    height = height_offset
                if idx == 0:
                    width += title_region[0]
                else:
                    if title_region[0] > W / 5:
                        mode = random.randint(0, 1)
                        if mode:
                            width += title_region[0] - int(0.2 * _width_text_region)
                        else:
                            width += title_region[0]

                    else:
                        width += title_region[0]

                # make a blank image for the text, initialized to transparent text color
                txt = Image.new('RGBA', im.size, (255, 255, 255, 0))
                fnt = ImageFont.truetype(list_font[idx], size_title)

                # get a drawing context
                d = ImageDraw.Draw(txt)
                coordinate_txt = (width, height)
                d.multiline_text(coordinate_txt, text=title, font=fnt, fill=list_color[idx], align='center')
                if debug:
                    txt.show()
                tmp[f"{idx}"] = txt

            txt = Image.alpha_composite(tmp["0"], tmp["1"])

            return txt

        else:
            # make a blank image for the text, initialized to transparent text color
            tmp = dict()
            height_title_region = title_region[3] - title_region[1]
            size_height_offset = 0
            size_width_offset = 0
            height_offset = 0

            size_title_2 = size_title

            height_title_all = height_title_region + 10
            _width_text_region = (title_region[2] - title_region[0])

            while height_title_all > height_title_region:
                for idx, title in enumerate(titles):
                    if idx == 0:
                        txt = Image.new('RGBA', im.size, (255, 255, 255, 0))
                        # Get param of title
                        fnt = ImageFont.truetype(list_font[idx], size_title)

                        # get a drawing context
                        d = ImageDraw.Draw(txt)
                        width_title, height_title = d.textsize(title, font=fnt, spacing=HEIGHT_OFFSET)
                        width = _width_center(width_text=width_title, width_img=_width_text_region)

                        # If width is False, auto resize size of title
                        while width is False:
                            size_title -= 1
                            # Get a font
                            fnt = ImageFont.truetype(list_font[idx], size_title)
                            width_title, height_title = d.textsize(title, font=fnt, spacing=HEIGHT_OFFSET)
                            width = _width_center(width_text=width_title, width_img=_width_text_region)

                        size_height_offset = height_title
                        size_width_offset = width_title

                    elif idx == 1:
                        txt = Image.new('RGBA', im.size, (255, 255, 255, 0))
                        # Get param of title
                        fnt = ImageFont.truetype(list_font[idx], size_title_2)

                        # get a drawing context
                        d = ImageDraw.Draw(txt)
                        width_title, height_title = d.textsize(title, font=fnt)

                        while width_title < size_width_offset:
                            size_title_2 += 1
                            # Get param of title
                            fnt = ImageFont.truetype(list_font[idx], size_title_2)

                            # get a drawing context
                            d = ImageDraw.Draw(txt)
                            width_title, height_title = d.textsize(title, font=fnt)
                            width = _width_center(width_text=width_title, width_img=_width_text_region)
                            if not width:
                                break
                        height_title_all = height_title + size_height_offset + 10

                        if height_title_all > title_region[3] - title_region[1]:
                            size_title -= 1

            for idx, title in enumerate(titles):
                if idx == 0:
                    txt = Image.new('RGBA', im.size, (255, 255, 255, 0))
                    # Get param of title
                    fnt = ImageFont.truetype(list_font[idx], size_title)

                    # get a drawing context
                    d = ImageDraw.Draw(txt)
                    width_title, height_title = d.textsize(title, font=fnt, spacing=HEIGHT_OFFSET)
                    width = _width_center(width_text=width_title, width_img=_width_text_region)

                    _height_im = title_region[3] - title_region[1]
                    height = title_region[1] + _height_center(height_title_all, _height_im)
                    height_offset = height + height_title + 10
                    width += title_region[0]

                    del txt, fnt

                    # make a blank image for the text, initialized to transparent text color
                    txt = Image.new('RGBA', im.size, (255, 255, 255, 0))
                    fnt = ImageFont.truetype(list_font[idx], size_title)

                    # get a drawing context
                    d = ImageDraw.Draw(txt)
                    coordinate_txt = (width, height)
                    d.multiline_text(coordinate_txt, text=title, font=fnt, fill=list_color[idx], align='center')
                    if debug:
                        txt.show()
                    tmp[f"{idx}"] = txt

                elif idx == 1:
                    txt = Image.new('RGBA', im.size, (255, 255, 255, 0))
                    # Get param of title
                    fnt = ImageFont.truetype(list_font[idx], size_title_2)

                    # get a drawing context
                    d = ImageDraw.Draw(txt)
                    width_title, height_title = d.textsize(title, font=fnt, spacing=HEIGHT_OFFSET)
                    width = _width_center(width_text=width_title, width_img=_width_text_region)
                    width += title_region[0]

                    coordinate_txt = (width, height_offset)
                    d.multiline_text(coordinate_txt, text=title, font=fnt, fill=list_color[idx], align='center')
                    if debug:
                        txt.show()
                    tmp[f"{idx}"] = txt

            txt = Image.alpha_composite(tmp["0"], tmp["1"])

            return txt
    else:
        return False


def draw_list_style_1(im_ob, text_region, path_output, js_txt, debug=False):
    """
Detail:
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

    title_region = []

    try:
        title = js_txt["title"]
        font_title = js_txt["path_font_title"]
        font_title_secondary = js_txt["path_font_title_secondary"]
        size_title = js_txt["size_title"]
        _color_title = js_txt["color_title"]
        color_title = _get_color(_color_title, 255)
        _color_title_secondary = js_txt["color_title_secondary"]
        color_title_secondary = _get_color(_color_title_secondary, 255)

        if color_title is False or color_title_secondary is False:
            result["content"] = f"{color_title} or {color_title_secondary} format is not True"
            return result

        # Get title region
        title_region = _title_region(text_region)
        title_img = False

        if not title_region:
            title = False
        else:

            # Check and draw title into image
            try:
                title_img = _draw_title(title=title, size_title=size_title,
                                        font_1=font_title, font_2=font_title_secondary,
                                        color_1=color_title, color_2=color_title_secondary,
                                        title_region=title_region, im=im, debug=debug)

            except Exception as error:
                print(error)
                title = False

            if not title_img:
                title = False

        # Set title status is True
        _title_status = True
    except:

        title = False
        height_offset_song = 2 * WIDTH_LINE

    # Get song region
    if title:
        song_region = _song_region(text_region, title_region)

    else:
        song_region = list(text_region)

    if not song_region:
        result["status"] = "error"
        result["content"] = "Can not get song region"

        return result

    # Adjust parameter text region
    song_region[1] = int((song_region[1]) + 2 * HEIGHT_OFFSET)

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
    max_width = 0   # The max long of list song
    height_song_top = int(song_region[1])  # The coordinate height song top
    height_song_bottom = int(song_region[3])    # The coordinate height song bottom
    width_song = int(song_region[0])    # The list coordinate of width song fl collum

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
    min_outside = 30

    for _index, song in enumerate(_list_song):

        _song_str = f"{_get_number(_index)}. {song['name']}\n"
        width_text, height_text = d.textsize(_song_str, font=fnt, spacing=space_line)
        _width_out = (song_region[2] - song_region[0] - 2 * EDGE_OFFSET) - width_text

        if _width_out <= 0:
            list_song.pop(_tmp_index)
            _tmp_index -= 1
        else:
            min_outside = min_outside if min_outside < _width_out else _width_out

        _tmp_index += 1

    count = 0

    while min_outside > 0:
        count += 1
        size_txt += 1
        fnt = ImageFont.truetype(font_song, size_txt)
        width_text, height_text = d.textsize(_song_str, font=fnt, spacing=space_line)
        _width_out = (song_region[2] - song_region[0] - 2 * EDGE_OFFSET) - width_text
        min_outside = min_outside if min_outside < _width_out else _width_out

        if min_outside < 0:
            size_txt -= 3

        if size_txt >= 35:
            break

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

    # Fix write over image when text region is right
    for max_width in list_max_width_img:
        width_coordinate = int((song_region[0] + song_region[2] - max_width)/2)

        if width_coordinate <= 5 and song_region[0] <= 10:
            width_coordinate = 10

        list_width_coordinate.append(width_coordinate)

    if debug:
        print(f"width_song is {width_song}")
        print(f"song_str is {song_str}")

# Draw song into the picture
    warring_status = False
    for img in range(count_img):
        song_img = Image.new('RGBA', im.size, (255, 255, 255, 0))
        fnt = ImageFont.truetype(font_song, size_txt)

        # get a drawing content
        d = ImageDraw.Draw(song_img)
        d.multiline_text((list_width_coordinate[img], height_song_top),
                         text=song_str[f'list_song_{img}'], font=fnt, fill=color,
                         align=align, spacing=space_line)

        if title is False:
            txt = song_img
        else:
            txt = Image.alpha_composite(song_img, title_img)

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


if __name__ == "__main__":

    im_ob = "./develop_env/object_test/jesus7.jpg"

    path_out = "./develop_env/output"
    text_region_1 = [(10, 0, 300, 720), (800, 0, 1070, 720)]
    text_region = [0, 0, 650, 720]

    try:
        with open('./develop_env/data/list_song.json') as json_file:
            data = json.load(json_file)
    except ValueError as error:
        print(error)

    result = draw_list_style_1(im_ob, text_region, path_output=path_out, js_txt=data, debug=True)
    print(result)