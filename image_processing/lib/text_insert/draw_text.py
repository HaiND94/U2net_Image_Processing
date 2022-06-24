import os
import random
import json
import configparser
import textwrap
import math

from PIL import Image, ImageFont, ImageDraw, ImageStat, ImageFilter
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


# Get the number of song:
def _get_number(i):
    num = str(i)
    if len(num) < 2:
        num = str(f"0{i}")

    return num


def create_rounded_rectangle_mask(rectangle, radius):
    # create mask image. all pixels set to translucent
    i = Image.new("RGBA", rectangle.size, (0, 0, 0, 0))
    # when using an image as mask only the alpha channel is important
    solid_fill = (50, 50, 50, 255)

    # create corner
    corner = Image.new('RGBA', (radius, radius), (0, 0, 0, 0))
    draw = ImageDraw.Draw(corner)
    # added the fill = .. you only drew a line, no fill
    draw.pieslice((0, 0, radius * 2, radius * 2), 180, 270, fill=solid_fill)

    # max_x, max_y
    mx, my = rectangle.size

    # paste corner rotated as needed
    # use corners alpha channel as mask

    i.paste(corner, (0, 0), corner)
    i.paste(corner.rotate(90), (0, my - radius),corner.rotate(90))
    i.paste(corner.rotate(180), (mx - radius,   my - radius),corner.rotate(180))
    i.paste(corner.rotate(270), (mx - radius, 0),corner.rotate(270))

    # draw both inner rects
    draw = ImageDraw.Draw(i)
    draw.rectangle([(radius, 0), (mx-radius, my)], fill=solid_fill)
    draw.rectangle([(0, radius), (mx, my-radius)], fill=solid_fill)

    return i


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


# Width center alignment
def _width_center(width_text, width_img):
    return int((width_img - width_text) / 2) if (width_img - width_text) > 0 else False


# Width center alignment
def _width_list_center(width_text, width_img, center):

    return int((center - width_text / 2)) if (width_text / 2 + center) < width_img else False


# Width left alignment
def _width_left(width_text, width_img, offset):
    return offset if (width_img - width_text) > 0 else False


# Width right alignment
def _width_right(width_text, width_img, offset):
    return (width_img - offset - width_text) if (width_img - width_text) > 0 else False


# Height alignment
def _height_center(size_text_height, height_img):
    return int((height_img - size_text_height) / 2)


def _height_top(size_text_height, height_img):
    return OFF_SET


def _height_bottom(size_text_height, height_img):
    return height_img - size_text_height - OFF_SET


# Sum of element list
def sum_list(list_):
    sum_ = 0
    for i in range(len(list_)):
        sum_ += list_[i]
    return sum_


# Get brightness of region of text
def _brightness(im_path, region):
    im = Image.open(im_path)
    im_ob = im.crop(region)
    stat = ImageStat.Stat(im_ob)
    try:
        r, g, b = stat.mean
    except:
        try:
            r, g, b, nope = stat.mean
        except:
            return False

    return math.sqrt(0.241 * (r ** 2) + 0.691 * (g ** 2) + 0.068 * (b ** 2))


# Get region of the text
def _text_region(width, height, width_text, height_text):
    # print(f"{width}*{height}*{width_text}*{height_text}")
    top = height
    right = width + width_text if (width_text + width) < W else W
    bottom = height + height_text if (height + height_text) < H else H
    left = width
    return left, top, right, bottom


# Get font
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


# Draw text follow one line into picture
def draw_text_one_line(im_ob, path_font, text, size_txt, path_output,
                       center_alignment=True, height_align="Bottom", show_img=False):
    """

    :param im_ob:
    :param path_font:
    :param text:
    :param size_txt:
    :param center_alignment:
    :param height_align:
    :return:
    """

    if (height_align in ['center', 'bottom', 'top']) is False:
        print('Height align format not True')
        return False

    if os.path.isdir(path_output) is False:
        print(f"{path_output} was not found")
        return False

    font = _get_font(path_font)

    if font is False:
        return False

    im = Image.open(im_ob).convert('RGBA')
    width_img, height_img = im.size
    new_size = _get_new_size(width_img, height_img)
    if new_size is False:
        pass
    else:
        width_img, height_img = new_size
        im = im.resize(new_size)

    # make a blank image for the text, initialized to transparent text color
    txt = Image.new('RGBA', im.size, (255, 255, 255, 0))

    # get a font
    fnt = ImageFont.truetype(font, size_txt)
    # get a drawing context
    d = ImageDraw.Draw(txt)
    width_text, height_text = d.textsize(text, font=fnt)

    if center_alignment:
        width = _width_center(width_text=width_text, width_img=width_img)
        while width is False:
            size_txt -= 1
            # get a font
            fnt = ImageFont.truetype(font, size_txt)
            width_text, height_text = d.textsize(text, font=fnt)
            width = _width_center(width_text=width_text, width_img=width_img)
    if height_align == 'bottom':
        height = _height_bottom(height_text, height_img)
    elif height_align == 'top':
        height = _height_top(height_text, height_img)
    elif height_align == 'center':
        height = _height_center(height_text, height_img)

    coordinate_txt = (width, height)

    region_text = (_text_region(width, height, width_text, height_text))
    brightness = _brightness(im_ob, region_text)
    if brightness > int(255/2):
        # Color is black
        color = (255, 0, 0, 255)
    else:
        # Color is white
        color = (255, 255, 255, 255)

    d.text(coordinate_txt, text=text, font=fnt, fill=color, align='center')

    out = Image.alpha_composite(im, txt)

    if show_img: out.show()
    time = datetime.now()
    current_time = time.strftime("%H:%M:%S")
    current_date = time.date()

    path_new = f"{path_output}/{current_date}_{current_time}.png"
    out.save(path_new)

    del out, im

    return path_new


# Draw text with multi line
def draw_text_multi_line(im_ob, path_font, path_output, text, size_txt, width_left, width_right, height_align="bottom",
                         show_img=False):

    if os.path.isdir(path_output) is False:
        print(f"{path_output} was not found")
        return False
    if (height_align in ['center', 'bottom', 'top']) is False:
        print('Height align format not True')
        return False
    if width_right > 1 or width_right < 0 or width_left < 0 or width_right > 1 or width_right < width_left:
        print('width right or width left value is false')
        return False

    font = _get_font(path_font)
    # font = path_font
    if font is False:
        return False

    im = Image.open(im_ob).convert('RGBA')
    if show_img: im.show()
    width_img, height_img = im.size
    new_size = _get_new_size(width_img, height_img)
    if new_size is False:
        pass
    else:
        width_img, height_img = new_size
        im = im.resize(new_size)

    max_digit = MAX_DIGIT
    min_digit = MIN_DIGIT
    _text = textwrap.fill(text, width=max_digit)

    # make a blank image for the text, initialized to transparent text color
    txt = Image.new('RGBA', im.size, (255, 255, 255, 0))

    # get a font
    try:
        fnt = ImageFont.truetype(font, size_txt)
    except Exception as error:
        print(error)
        return False
    # get a drawing context
    d = ImageDraw.Draw(txt)
    width_text, height_text = d.textsize(_text, font=fnt)
    distance = (width_right - width_left)*width_img
    while width_text > distance or height_text < height_text:
        if height_text < height_text:
            size_txt -= 1
        else:
            if max_digit > min_digit:
                max_digit -= 1
        _text = textwrap.fill(text, width=max_digit)
        fnt = ImageFont.truetype(font, size_txt)
        # get a drawing context
        d = ImageDraw.Draw(txt)
        width_text, height_text = d.textsize(_text, font=fnt)
    # width = width_left*width_img
    width = _width_center(width_text=width_text, width_img=width_img)
    if height_align == 'bottom':
        height = _height_bottom(height_text, height_img - 100)
    elif height_align == 'top':
        height = _height_top(height_text, 40)
    elif height_align == 'center':
        height = _height_center(height_text, height_img)

    coordinate_txt = (width, height)
    region_text = (_text_region(width, height, width_text, height_text))
    brightness = _brightness(im_ob, region_text)

    if brightness > int(510/3):
        # Color is black
        color = (0, 0, 0, 255)
    elif brightness <= int(255/3):
        # Color is white
        color = (255, 255, 255, 255)
    else:
        # Color is red
        color = (255, 0, 0, 255)

    d.multiline_text(coordinate_txt, text=_text, font=fnt, fill=color, align='center')

    out = Image.alpha_composite(im, txt)

    time = datetime.now()
    current_time = time.strftime("%H:%M:%S")
    current_date = time.date()

    path_new = f"{path_output}/{current_date}_{current_time}.png"
    if show_img:
        out.show()
    try:
        out.save(path_new)
    except Exception as error:
        print(error)
        return False

    del out, d, im, im_ob

    return path_new


# Draw text for play list
def _draw_list(im_ob, path_font_title, path_font_song, black_zone,
              path_output, js_txt, size_text=25, size_title=50,
              template="list", width_ob=160, alignment='left', show_img=False):
    """
    Detail :
    :param im_ob:
    :param path_font_title:
    :param path_font_song:
    :param black_zone:
    :param path_output:
    :param js_txt:
    :param size_text:
    :param size_title:
    :param alignment:
    :param show_img:
    :return:
    """

    # check conditional
    if os.path.isdir(path_output) is False:
        print(f"Cannot find {path_output}")
        return False

    if alignment not in ['center', 'right', 'left']:
        print("align must be center or right or left")
        return False

    if len(black_zone) > 2:
        print("Black zone format not true")
        return False
    elif len(black_zone) < 2:
        min_black = 0
        max_black = 0
    else:
        min_black = min(black_zone) - 10
        max_black = max(black_zone) + 10

    if js_txt is None:
        print("No json file import")
        return False

    try:
        title = js_txt["title"]
        sum = js_txt["sum"]
        list_song = js_txt["list_songs"]
        if len(list_song) != sum:
            print("Data is wrong")
            return False
    except AttributeError as error:
        print(error)
        return False

    font_title = _get_font(path_font_title)
    font_song = _get_font(path_font_song)

    if font_song is False or font_song is False:
        return False

    if (font_song and font_title) is False:
        print("Font file or folder not found!")
        return False

    im = Image.open(im_ob).convert('RGBA')
    width_img, height_img = im.size
    new_size = _get_new_size(width_img, height_img)
    if new_size is False:
        pass
    else:
        width_img, height_img = new_size
        im = im.resize(new_size)

    # make a blank image for the text, initialized to transparent text color
    txt = Image.new('RGBA', im.size, (255, 255, 255, 0))

# Get param of title
    fnt = ImageFont.truetype(font_title, size_title)
    # get a drawing context
    d = ImageDraw.Draw(txt)
    width_title, height_text = d.textsize(title, font=fnt)

# Draw song into image
    # Create new param
    max_width = 0
    height_song = HEIGHT_OFF_SONG + height_text*1.5
    width_song = [40]
    size_txt = size_text
    fnt = ImageFont.truetype(font_song, size_txt)
    # get a drawing content
    d = ImageDraw.Draw(txt)

    height_text = 0
    width_text = 0
    song_str = {}
    stop = False
    # width_col = []
    # The col
    i = 0
    # The song number
    j = 0

    while j < len(list_song):   # Not finish list

        # To save list song follow collum
        song_str[f'col_{i}'] = ''

        while (height_img - height_song - height_text - 10) > 0:    # Check end of the height image
            # Calculator width of collum i
            song_str[f'col_{i}'] += f"{j + 1}. {list_song[j]['name']}\n"
            width_text, height_text = d.textsize(song_str[f'col_{i}'], font=fnt)
            max_width = width_text if width_text > max_width else max_width

            if i != 0:
                if alignment == 'left':
                    if (min_black - width_song[i] - max_width) < 0:
                        stop = True
                        j -= 1
                        break

                if alignment == 'right':
                    if (width_img - width_song[i] - max_black - max_width) < 0:
                        j -= 1
                        stop = True
                        break

            j += 1
            if j >= len(list_song):
                break

        if stop:
            if tem != i:
                width_song.pop(i)
            break

        tem = i

        # width_col.append(max_width)
        if j < len(list_song):
            width_song.append(int(max_width * 1.1) + width_song[i])

        i += 1
        height_text = 0

    if alignment == "right":
        for l in range(len(width_song)):
            width_song[l] += width_ob - 10

    # Draw multi line in to the picture

    _color_status = False
    if i == 0:
        return False

    if i != 1:
        if alignment == "left":
            region_text = (0, height_song - 25, width_song[-1] + max_width + 25, H)
        elif alignment == "right":
            region_text = (width_song[0] - 20, height_song - 25, W, H)
        _new_im = im.crop(region_text)
        _new_im = _new_im.filter(ImageFilter.GaussianBlur(10)).convert("RGBA")
        im.paste(_new_im, (int(region_text[0]), int(region_text[1])))

    for k in range(i):

        width_text, height_text = d.textsize(song_str[f'col_{k}'], font=fnt)
        region_text = _text_region(width_song[k], height_song, width_text, height_text)
        len_of_col = int(region_text[2] - region_text[0])

        if _color_status is False:
            try:
                brightness = _brightness(im_ob, region_text)
            except Exception as error:
                print(error)
                brightness = 200
            if brightness > int(510/3):
                # Color is black
                color = (0, 0, 0, 255)
            else:
                # Color is white
                color = (255, 255, 255, 255)

        if i == 1 and alignment == 'left':
            region_text = (0.15 * W - 25, height_song - 25, width_text + 0.15 * W + 25, height_song + height_text + 25)
            _new_im = im.crop(region_text)
            _new_im = _new_im.filter(ImageFilter.GaussianBlur(108)).convert("RGBA")
            im.paste(_new_im, (int(region_text[0]), int(region_text[1])))
            d.multiline_text((0.15 * W, height_song), text=song_str[f'col_{k}'], font=fnt, fill=color, align='left')

        elif i == 1 and alignment == 'right':
            region_text = (0.6 * W - 25, height_song - 25, width_text + 0.6 * W + 25, height_song + height_text + 25)
            _new_im = im.crop(region_text)
            _new_im = _new_im.filter(ImageFilter.GaussianBlur(108)).convert("RGBA")
            im.paste(_new_im, (int(region_text[0]), int(region_text[1])))
            d.multiline_text((0.6 * W, height_song), text=song_str[f'col_{k}'], font=fnt, fill=color, align='left')

        else:
            d.multiline_text((width_song[k], height_song), text=song_str[f'col_{k}'], font=fnt, fill=color,
                             align='left')

# Draw tile:
    if i != 1:
        # Alignment text follow require
        center_song = int((width_song[0] + width_song[-1] + len_of_col)/2)
        # print(center_song)
        width = _width_list_center(width_text=width_title, width_img=width_img,
                                   center=center_song)
    else:
        width = False
    # print(width)
    if width is False:
        width = _width_center(width_text=width_title, width_img=width_img)
        # Fix size text with into picture
        while width is False:
            size_title -= 1
            # get a font
            fnt = ImageFont.truetype(font_title, size_title)
            width_text, height_text = d.textsize(title, font=fnt)
            width = _width_center(width_text=width_text, width_img=width_img)
    # else:
    fnt = ImageFont.truetype(font_title, size_title)
    width_text, height_text = d.textsize(title, font=fnt)

    # Set height in top off image
    height = 30

    # Draw underline and tile:
    coordinate_txt = (width, height)

    _draw = ImageDraw.Draw(txt)

    _draw.line((width + WIDTH_OFFSET, height + HEIGHT_OFFSET + height_text,
                width + width_text - WIDTH_OFFSET, height + HEIGHT_OFFSET + height_text),
               width=5, fill=(255, 255, 255, 255))
    # txt = txt.filter(ImageFilter.GaussianBlur(2))

    region_text = _text_region(width, height, width_text, height_text)
    brightness = _brightness(im_ob, region_text)

    if brightness > int(510 / 3):
        # Color is black
        color = (0, 0, 0, 255)
    elif brightness <= int(255 / 3):
        # Color is white
        color = (255, 255, 255, 255)
    else:
        # Color is red
        color = (255, 0, 0, 255)

    d = ImageDraw.Draw(txt)
    d.text(coordinate_txt, text=title, font=fnt, fill=color, align='center')

    out = Image.alpha_composite(im, txt)
    if show_img:
        out.show()

    time = datetime.now()
    current_time = time.strftime("%H:%M:%S")
    current_date = time.date()

    path_new = f"{path_output}/{current_date}_{current_time}.png"

    try:
        out.save(path_new)
    except Exception as error:
        print(error)
        return False

    return path_new


# Draw text for play list
def draw_list(im_ob, path_font_title, path_font_song, black_zone,
              path_output, js_txt, size_text=25, size_title=50,
              template = "list", width_ob=160, alignment='left', show_img=False):
    """
    Detail :
    :param im_ob:
    :param path_font_title:
    :param path_font_song:
    :param black_zone:
    :param path_output:
    :param js_txt:
    :param size_text:
    :param size_title:
    :param alignment:
    :param show_img:
    :return:
    """

    # check conditional
    if os.path.isdir(path_output) is False:
        print(f"Cannot find {path_output}")
        return False

    if alignment not in ['center', 'right', 'left']:
        print("align must be center or right or left")
        return False

    # if len(black_zone) > 2:
    #     print("Black zone format not true")
    #     return False
    # elif len(black_zone) < 2:
    #     min_black = 0
    #     max_black = 0
    # else:
    #     min_black = min(black_zone) - 10
    #     max_black = max(black_zone) + 10

    if js_txt is None:
        print("No json file import")
        return False

    try:
        title = js_txt["title"]
        sum = js_txt["sum"]
        list_song = js_txt["list_songs"]
        if len(list_song) != sum:
            print("Data is wrong")
            return False
    except AttributeError as error:
        print(error)
        return False

    try:
        offset_song = js_txt["offset"]
    except:
        offset_song = 1

    font_title = _get_font(path_font_title)
    font_song = _get_font(path_font_song)

    if (font_song and font_title) is False:
        print("Font file or folder not found!")
        return False

    if width_ob > (2 * W / 3):
        width_ob = 2 * W / 3

    im = Image.open(im_ob).convert('RGBA')
    width_img, height_img = im.size
    new_size = _get_new_size(width_img, height_img)
    if new_size is False:
        pass
    else:
        width_img, height_img = new_size
        im = im.resize(new_size)

    # make a blank image for the text, initialized to transparent text color
    txt = Image.new('RGBA', im.size, (255, 255, 255, 0))

    # Get param of title
    fnt = ImageFont.truetype(font_title, size_title)
    # get a drawing context
    d = ImageDraw.Draw(txt)
    width_title, height_text = d.textsize(title, font=fnt)

# Draw song into image
    # Create new param
    max_width = 0
    height_song = HEIGHT_OFF_SONG + height_text*1.5
    width_song = [40]
    size_txt = size_text
    fnt = ImageFont.truetype(font_song, size_txt)
    # get a drawing content
    d = ImageDraw.Draw(txt)

    height_text = 0
    width_text = 0
    song_str = {}
    stop = False
    # width_col = []
    # The col
    i = 0
    # The song number
    j = 0
    sum_song = 0

    while j < len(list_song):   # Not finish list

        # To save list song follow collum
        song_str[f'col_{i}'] = ''

        while (height_img - height_song - height_text - 10) > 0:    # Check end of the height image
            # Calculator width of collum i
            song_str[f'col_{i}'] += f"{_get_number(j + offset_song)}. {list_song[j]['name']}\n"
            width_text, height_text = d.textsize(song_str[f'col_{i}'], font=fnt)
            max_width = width_text if width_text > max_width else max_width
            sum_song += 1
            if i != 0:
                if alignment == 'left':
                    if (W - width_ob - width_song[i] - max_width - EDGE_OFFSET) < 0:
                        stop = True
                        j -= 1
                        break

                if alignment == 'right':
                    if (width_img - width_song[i] - width_ob - max_width - EDGE_OFFSET) < 0:
                        j -= 1
                        stop = True
                        break

            j += 1
            if j >= len(list_song):
                break

        if stop:
            if tem != i:
                width_song.pop(i)
                sum_song -= 1
            break

        tem = i

        # width_col.append(max_width)
        if j < len(list_song):
            width_song.append(int(max_width * 1.1) + width_song[i])

        i += 1
        height_text = 0

    if alignment == "right":
        for l in range(len(width_song)):
            width_song[l] += width_ob + EDGE_OFFSET

    # Draw multi line in to the picture

    _color_status = False
    if i == 0:
        return False

    if i > 1:
        range_text_song = width_song[-1] - width_song[0] + max_width
    else:
        range_text_song = max_width

    _width_col0 = 30
    if alignment == "left":
        _width_col0 = int((W - width_ob - EDGE_OFFSET - range_text_song) / 2)
    elif alignment == "right":
        _width_col0 = int((W - width_ob - EDGE_OFFSET - range_text_song) / 2)

    for idx, width in enumerate(width_song):
        width_song[idx] = width + _width_col0

    for k in range(i):

        width_text, height_text = d.textsize(song_str[f'col_{k}'], font=fnt)
        region_text = _text_region(width_song[k], height_song, width_text, height_text)
        len_of_col = int(region_text[2] - region_text[0])

        if _color_status is False:
            try:
                brightness = _brightness(im_ob, region_text)
            except Exception as error:
                print(error)
                pass
            if brightness is False:
                brightness = 0
            if brightness > int(510/3):
                # Color is black
                color = (0, 0, 0, 255)
                _color_status = True
            else:
                # Color is white
                color = (255, 255, 255, 255)
                _color_status = True

        if i == 1 and alignment == 'left':
            region_text = (0.15 * W - 25, height_song - 25, width_text + 0.15 * W + 25, height_song + height_text + 25)
            # _new_im = im.crop(region_text)
            # _new_im = _new_im.filter(ImageFilter.GaussianBlur(5)).convert("RGBA")
            # im.paste(_new_im, (int(region_text[0]), int(region_text[1])))
            d.multiline_text((width_song[k], height_song), text=song_str[f'col_{k}'], font=fnt, fill=color, align='left')

        elif i == 1 and alignment == 'right':
            region_text = (0.6 * W - 25, height_song - 25, width_text + 0.6 * W + 25, height_song + height_text + 25)

            d.multiline_text((width_song[k], height_song), text=song_str[f'col_{k}'], font=fnt, fill=color, align='left')

        else:
            d.multiline_text((width_song[k], height_song), text=song_str[f'col_{k}'], font=fnt, fill=color,
                             align='left')

# Draw tile:
    if i != 1:
        # Alignment text follow require
        center_song = int((width_song[0] + width_song[-1] + len_of_col)/2)
        # print(center_song)
        width = _width_list_center(width_text=width_title, width_img=width_img,
                                   center=center_song)
    else:
        width = False
    # print(width)
    if width is False:
        width = _width_center(width_text=width_title, width_img=width_img)
        # Fix size text with into picture
        while width is False:
            size_title -= 1
            # get a font
            fnt = ImageFont.truetype(font_title, size_title)
            width_text, height_text = d.textsize(title, font=fnt)
            width = _width_center(width_text=width_text, width_img=width_img)
    # else:
    fnt = ImageFont.truetype(font_title, size_title)
    width_text, height_text = d.textsize(title, font=fnt)

    # Set height in top off image
    height = 30

    # Draw underline and tile:
    coordinate_txt = (width, height)

    _draw = ImageDraw.Draw(txt)

    _draw.line((width + WIDTH_OFFSET, height + HEIGHT_OFFSET + height_text,
                width + width_text - WIDTH_OFFSET, height + HEIGHT_OFFSET + height_text),
               width=5, fill=(255, 255, 255, 255))
    # txt = txt.filter(ImageFilter.GaussianBlur(2))

    region_text = _text_region(width, height, width_text, height_text)
    brightness = _brightness(im_ob, region_text)

    if brightness > int(510 / 3):
        # Color is black
        color = (0, 0, 0, 255)
    elif brightness <= int(255 / 3):
        # Color is white
        color = (255, 255, 255, 255)
    else:
        # Color is red
        color = (255, 0, 0, 255)

    d = ImageDraw.Draw(txt)
    d.text(coordinate_txt, text=title, font=fnt, fill=color, align='center')

    out = Image.alpha_composite(im, txt)
    if show_img:
        out.show()

    time = datetime.now()
    current_time = time.strftime("%H:%M:%S")
    current_date = time.date()

    path_new = f"{path_output}/{current_date}_{current_time}.png"

    try:
        out.save(path_new)
    except Exception as error:
        print(error)
        return False

    # if i == 1:
    #     sum_song = len()
    # elif sum_song == len(list_song):
    #     pass
    # else:
    #     sum_song = sum_song - 1

    result = (path_new, sum_song)

    del out, time, current_time, current_date, d, _draw, fnt, im

    return result


def draw_song(im_ob, path_font_song, text_region,
              path_output, js_txt, size_txt=25,
              show_img=False):
    # check conditional
    if os.path.isdir(path_output) is False:
        print(f"Cannot find {path_output}")
        return False

    if len(text_region) != 4:
        print("Black zone format not true")
        return False

    if js_txt is None:
        print("No json file import")
        return False

    try:
        sum = js_txt["sum"]
        list_song = js_txt["list_songs"]
        if len(list_song) != sum:
            print("Data is wrong")
            return False
    except Exception as error:
        print(error)
        return False

    try:
        offset_song = js_txt["offset"]
    except:
        offset_song = 1

    font_song = _get_font(path_font_song)

    if font_song is False:
        print("Font file or folder not found!")
        return False

    if show_img:
        print(text_region)

    im = Image.open(im_ob).convert('RGBA')
    width_img, height_img = im.size

    alignment = "left"

    new_size = _get_new_size(width_img, height_img)
    if new_size is False:
        pass
    else:
        width_img, height_img = new_size
        im = im.resize(new_size)

    # make a blank image for the text, initialized to transparent text color
    txt = Image.new('RGBA', im.size, (255, 255, 255, 0))

# Draw song into image
    # Create new param
    max_width = 0
    height_song_top = text_region[1]
    height_song_bottom = text_region[3]
    width_song = [text_region[0]]

    fnt = ImageFont.truetype(font_song, size_txt)
    # get a drawing content
    d = ImageDraw.Draw(txt)

    height_text = 0
    width_text = 0
    song_str = {}
    stop = False
    # width_col = []
    # The col
    i = 0
    # The song number
    j = 0
    sum_song = 0

    while j < len(list_song):  # Not finish list

        # To save list song follow collum
        song_str[f'col_{i}'] = ''

        while (height_song_bottom - height_song_top - height_text) > 0:  # Check end of the height image
            # Calculator width of collum i
            song_str[f'col_{i}'] += f"{_get_number(offset_song + j)}. {list_song[j]['name']}\n"
            width_text, height_text = d.textsize(song_str[f'col_{i}'], font=fnt)
            max_width = width_text if width_text > max_width else max_width
            sum_song += 1
            if i != 0:
                if alignment == 'left':
                    if (W - text_region[2] - width_song[i] - max_width - EDGE_OFFSET) < 0:
                        stop = True
                        j -= 1
                        break

                if alignment == 'right':
                    if (width_img - width_song[i] - text_region[2] - max_width - EDGE_OFFSET) < 0:
                        j -= 1
                        stop = True
                        break

            j += 1
            if j >= len(list_song):
                break

        if stop:
            if tem != i:
                width_song.pop(i)
                sum_song -= 1
            break

        tem = i

        # width_col.append(max_width)
        if j < len(list_song):
            width_song.append(int(max_width * 1.1) + width_song[i])

        i += 1
        height_text = 0

    if show_img:
        print(width_song)
    # Draw multi line in to the picture

    _color_status = False
    if i == 0:
        return False

    if show_img:
        print(width_song)

    if i == 1:
        width_song[0] = width_song[0] + int((text_region[2] - text_region[0] - max_width + 10) / 2)
    for k in range(i):

        width_text, height_text = d.textsize(song_str[f'col_{k}'], font=fnt)
        region_text = _text_region(width_song[k], height_song_top, width_text, height_text)

        if _color_status is False:
            try:
                brightness = _brightness(im_ob, region_text)
            except Exception as error:
                print(error)
                pass
            if brightness is False:
                brightness = 0
            if brightness > int(510 / 3):
                # Color is black
                color = (0, 0, 0, 255)
                _color_status = True
            else:
                # Color is white
                color = (255, 255, 255, 255)
                _color_status = True

        if i == 1 and alignment == 'left':
            d.multiline_text((width_song[k], height_song_top), text=song_str[f'col_{k}'], font=fnt, fill=color,
                             align='left')

        elif i == 1 and alignment == 'right':

            d.multiline_text((width_song[k], height_song_top), text=song_str[f'col_{k}'], font=fnt, fill=color,
                             align='left')

        else:
            d.multiline_text((width_song[k], height_song_top), text=song_str[f'col_{k}'], font=fnt, fill=color,
                             align='left')

    if show_img:
        print(width_song)

    out = Image.alpha_composite(im, txt)
    if show_img:
        out.show()

    time = datetime.now()
    current_time = time.strftime("%H:%M:%S")
    current_date = time.date()

    path_new = f"{path_output}/{current_date}_{current_time}.png"

    try:
        out.save(path_new)
    except Exception as error:
        print(error)
        return False

    result = (path_new, sum_song)

    del out, time, current_time, current_date, fnt, im

    return result


def draw_template_symmetry(im_ob, path_font_song, path_font_singer, text_region,
                           path_output, js_txt, size_txt=25,
                           show_img=False):
    """

    :param im_ob:
    :param path_font_song:
    :param path_font_singer:
    :param text_region:
    :param path_output:
    :param js_txt:
    :param size_txt:
    :param show_img:
    :return:
    """
    # check conditional
    if os.path.isdir(path_output) is False:
        print(f"Cannot find {path_output}")
        return False

    if len(text_region) != 4:
        print("Black zone format not true")
        return False

    if js_txt is None:
        print("No json file import")
        return False

    try:
        sum = js_txt["sum"]
        list_song = js_txt["list_songs"]
        list_singer = js_txt["list_singer"]
        if len(list_song) != sum:
            print("Data is wrong")
            return False
    except Exception as error:
        print(error)
        return False

    try:
        offset_song = js_txt['offset']
    except:
        offset_song = 1

    try:
        mode = js_txt["mode"]
        if mode not in ["line", "no_line"]:
            print(f"{js_txt['mode']} must have line or no_line")
            return False
    except:
        mode = "singer"

    color = (255, 255, 255, 255)
    font_song = _get_font(path_font_song)
    font_singer = _get_font(path_font_singer)

    if font_song is False or font_singer is False:
        print("Font file or folder not found!")
        return False

    if show_img:
        print(text_region)

    text_region = list(text_region)
    text_region[1] = int(text_region[1]) + 2 * WIDTH_LINE

    im = Image.open(im_ob).convert('RGBA')
    width_img, height_img = im.size

    alignment = "left"

    new_size = _get_new_size(width_img, height_img)
    if new_size is False:
        pass
    else:
        width_img, height_img = new_size
        im = im.resize(new_size)

    # make a blank image for the text, initialized to transparent text color
    txt = Image.new('RGBA', im.size, (255, 255, 255, 0))

    _fnt_song = ImageFont.truetype(font_song, size_txt)
    _d_song = ImageDraw.Draw(txt)
    _width_text, _height_text = _d_song.textsize('test', font=_fnt_song)
    del _d_song, txt

    space_line = 1.5 * _height_text
    _height_singer = _height_text
    _size_singer = size_txt

    if show_img:
        print(space_line)

    txt = Image.new('RGBA', im.size, (255, 255, 255, 0))
    d = ImageDraw.Draw(txt)

    while _height_singer > ((4 * _height_text) / 5):
        _size_singer -= 1
        fnt = ImageFont.truetype(font_singer, _size_singer)
        # get a drawing content
        _width_singer, _height_singer = d.textsize("test", font=fnt)

    if show_img:
        print(f"size of singer is {_size_singer}")

# Draw song into image
    # Create new param
    max_width = 0
    height_song_top = int(text_region[1])
    height_song_bottom = int(text_region[3])
    width_song = []
    _with_song = int(((text_region[2]) - text_region[0]) / 3) + text_region[0]
    width_song.append(_with_song)

    if show_img:
        print(width_song)

    fnt = ImageFont.truetype(font_song, size_txt)
    # get a drawing content
    d = ImageDraw.Draw(txt)

    height_text = 0
    song_str = {}
    stop = False
    i = 0
    # The song number
    j = 0
    sum_song = 0

    while j < len(list_song):  # Not finish list

        # To save list song follow collum
        song_str[f'col_{i}'] = ''

        while (height_song_bottom - height_song_top - height_text) > 0:  # Check end of the height image
            # Calculator width of collum i
            song_str[f'col_{i}'] += f"{_get_number(j + offset_song)}. {list_song[j]['name']}\n"
            width_text, height_text = d.textsize(song_str[f'col_{i}'] + "\n", font=fnt, spacing=space_line)
            max_width = width_text if width_text > max_width else max_width
            sum_song += 1
            if i != 0:
                if alignment == 'left':
                    if (W - text_region[2] - width_song[i] - max_width - EDGE_OFFSET) < 0:
                        stop = True
                        j -= 1
                        break

                if alignment == 'right':
                    if (width_img - width_song[i] - text_region[2] - max_width - EDGE_OFFSET) < 0:
                        j -= 1
                        stop = True
                        break

            j += 1
            if j >= len(list_song):
                break

        if stop:
            if tem != i:
                width_song.pop(i)
                sum_song -= 1
            break

        tem = i
        if i > 1:
            i = 1
            break

        # width_col.append(max_width)
        if j < len(list_song):
            width_song.append(int(max_width * 1.1) + width_song[i])

        i += 1
        height_text = 0

    if show_img:
        print(width_song)
    # Draw multi line in to the picture

    _color_status = False
    if i == 0:
        return False

    if show_img:
        print(width_song)

    for k in range(i):

        width_text, height_text = d.textsize(song_str[f'col_{k}'], font=fnt, spacing=size_txt)

        region_text = _text_region(width_song[k], height_song_top, width_text, height_text)

        if _color_status is False:
            try:
                brightness = _brightness(im_ob, region_text)
                _color_status = True
            except Exception as error:
                print(error)
                pass
            if brightness is False:
                brightness = 0
            if brightness > int(510 / 3):
                # Color is black
                # color = (5, 5, 5, 180)
                color = (255, 255, 255, 255)
            else:
                # Color is white
                color = (255, 255, 255, 255)

    if show_img:
        print(width_song)


# Draw singer
    text_singer = ''
    _singer_color = color
    fnt = ImageFont.truetype(font_singer, _size_singer)
    # get a drawing content
    d = ImageDraw.Draw(txt)
    _offset_line = space_line - _height_singer

    if show_img:
        print(f"the number of song in one page {j}")

    for index in range(sum_song):
        text_singer += f"{list_singer[index]['name']}\n"

    _width_tmp, _height_tmp = d.textsize(text_singer, font=fnt)
    if show_img:
        print(f"mode is {mode}")

    if mode != "singer":

        if (text_region[2] - text_region[0]) > (_width_tmp + max_width):

            if mode == "no_line":
                # Draw with no line
                _width_singer = width_song[0] - _width_tmp + 5

                if show_img:
                    print(_width_singer)
                    print(_width_tmp)
                spacing = _offset_line + _height_text

                d.multiline_text((_width_singer, height_song_top + _height_text + int(_offset_line/2)),
                                 text=text_singer, font=fnt, fill=_singer_color, align="right", spacing=spacing)
            if mode == "line":
                # Draw with line
                _width_singer = width_song[0] - _width_tmp - WIDTH_LINE * 5
                if _width_singer < 0:
                    print("text too long")
                    return False

                if show_img:
                    print(_width_singer)
                    print(_width_tmp)
                spacing = _offset_line + _height_text
                d.multiline_text((_width_singer, height_song_top + _height_text + int(_offset_line / 2)),
                                 text=text_singer, font=fnt, fill=_singer_color, align="right", spacing=spacing)

                line_xy_1 = (width_song[0] - WIDTH_LINE * 2 + LONG_WIDTH,
                             height_song_top - int(0.4 * spacing))
                line_xy_2 = (width_song[0] - WIDTH_LINE * 2,
                             height_song_top - int(0.4 * spacing))
                line_xy_3 = (width_song[0] - WIDTH_LINE * 2,
                             height_song_top + height_text + int(0.8 * spacing))
                line_xy_4 = (width_song[0] - WIDTH_LINE * 2 - LONG_WIDTH,
                             height_song_top + height_text + int(0.8 * spacing))

                d_line = ImageDraw.Draw(txt)
                d_line.line([line_xy_1, line_xy_2, line_xy_3, line_xy_4],
                            fill=(255, 250, 248), width=2)
                if show_img:
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
        width_song[0] = text_region[0] + int((text_region[2] - text_region[0] - _width_tmp)/2)
        if show_img:
            print(width_song)

        d.multiline_text((width_song[0] + 5, height_song_top + _height_text + int(_offset_line / 2)),
                         text=text_singer, font=fnt, fill=_singer_color, align="left", spacing=spacing)

# Draw song into the picture
    fnt = ImageFont.truetype(font_song, size_txt)
    # get a drawing content
    d = ImageDraw.Draw(txt)
    for k in range(i):
        d.multiline_text((width_song[0], height_song_top),
                         text=song_str[f'col_{k}'], font=fnt, fill=color,
                         align='left', spacing=space_line)

    out = Image.alpha_composite(im, txt)
    if show_img:
        out.show()

    time = datetime.now()
    current_time = time.strftime("%H:%M:%S")
    current_date = time.date()

    path_new = f"{path_output}/{current_date}_{current_time}.png"

    try:
        out.save(path_new)
    except Exception as error:
        print(error)
        return False

    result = (path_new, sum_song)

    del out, time, current_time, current_date, fnt, im

    return result


def draw_template_collum(im_ob, path_font_song, path_font_singer, text_region,
                         path_output, js_txt, size_txt=25,
                         show_img=False):
    """

    :param im_ob:
    :param path_font_song:
    :param path_font_singer:
    :param text_region:
    :param path_output:
    :param js_txt:
    :param size_txt:
    :param show_img:
    :return:
    """
    # check conditional
    if os.path.isdir(path_output) is False:
        print(f"Cannot find {path_output}")
        return False

    if len(text_region) != 4:
        print("Black zone format not true")
        return False

    if js_txt is None:
        print("No json file import")
        return False

    try:
        sum = js_txt["sum"]
        list_song = js_txt["list_songs"]
        list_singer = js_txt["list_singer"]
        if len(list_song) != sum:
            print("Data is wrong")
            return False
    except Exception as error:
        print(error)
        return False

    try:
        offset_song = js_txt['offset']
    except:
        offset_song = 1

    color = (255, 255, 255, 255)
    font_song = _get_font(path_font_song)
    font_singer = _get_font(path_font_singer)

    if font_song is False or font_singer is False:
        print("Font file or folder not found!")
        return False

    if show_img:
        print(text_region)

    im = Image.open(im_ob).convert('RGBA')
    width_img, height_img = im.size

    alignment = "left"

    # if width_img != W or height_img != H:
    #     print("size of image not True")
    #     return False

    new_size = _get_new_size(width_img, height_img)
    if new_size is False:
        pass
    else:
        width_img, height_img = new_size
        im = im.resize(new_size)

    # make a blank image for the text, initialized to transparent text color
    txt = Image.new('RGBA', im.size, (255, 255, 255, 0))

    _fnt_song = ImageFont.truetype(font_song, size_txt)
    _d_song = ImageDraw.Draw(txt)
    _width_text, _height_text = _d_song.textsize('test', font=_fnt_song)
    del _d_song, txt

    space_line = 1.5 * _height_text
    _height_singer = _height_text
    _size_singer = size_txt

    if show_img:
        print(space_line)

    txt = Image.new('RGBA', im.size, (255, 255, 255, 0))
    d = ImageDraw.Draw(txt)

    while _height_singer > ((4 * _height_text) / 5):
        _size_singer -= 1
        fnt = ImageFont.truetype(font_singer, _size_singer)
        # get a drawing content
        _width_singer, _height_singer = d.textsize("test", font=fnt)

    if show_img:
        print(f"size of singer is {_size_singer}")

# Draw song into image
    # Create new param
    max_width = 0
    height_song_top = text_region[1]
    height_song_bottom = text_region[3]
    width_song = []
    _with_song = int((text_region[2] - text_region[0]) / 3) + text_region[0]
    width_song.append(_with_song)

    if show_img:
        print(width_song)

    fnt = ImageFont.truetype(font_song, size_txt)
    # get a drawing content
    d = ImageDraw.Draw(txt)

    height_text = 0
    song_str = {}
    stop = False
    i = 0
    # The song number
    j = 0
    sum_song = 0

    while j < len(list_song):  # Not finish list

        # To save list song follow collum
        song_str[f'col_{i}'] = ''

        while (height_song_bottom - height_song_top - height_text) > 0:  # Check end of the height image
            # Calculator width of collum i
            song_str[f'col_{i}'] += f"{_get_number(j + offset_song)}. {list_song[j]['name']}"
            width_text, height_text = d.textsize(song_str[f'col_{i}'], font=fnt, spacing=space_line)
            max_width = width_text if width_text > max_width else max_width
            sum_song += 1
            if i != 0:
                if alignment == 'left':
                    if (W - text_region[2] - width_song[i] - max_width - EDGE_OFFSET) < 0:
                        stop = True
                        j -= 1
                        break

                if alignment == 'right':
                    if (width_img - width_song[i] - text_region[2] - max_width - EDGE_OFFSET) < 0:
                        j -= 1
                        stop = True
                        break

            j += 1
            if j >= len(list_song):
                break

        if stop:
            if tem != i:
                width_song.pop(i)
                sum_song -= 1
            break

        tem = i
        if i > 1:
            i = 1
            break

        # width_col.append(max_width)
        if j < len(list_song):
            width_song.append(int(max_width * 1.1) + width_song[i])

        i += 1
        height_text = 0

    if show_img:
        print(width_song)
    # Draw multi line in to the picture

    _color_status = False
    if i == 0:
        return False

    if show_img:
        print(width_song)

    for k in range(i):

        width_text, height_text = d.textsize(song_str[f'col_{k}'], font=fnt, spacing=size_txt)

        region_text = _text_region(width_song[k], height_song_top, width_text, height_text)

        if _color_status is False:
            try:
                brightness = _brightness(im_ob, region_text)
                _color_status = True
            except Exception as error:
                print(error)
                pass
            if brightness is False:
                brightness = 0
            if brightness > int(510 / 3):
                # Color is black
                # color = (5, 5, 5, 180)
                color = (250, 250, 250, 200)
            else:
                # Color is white
                color = (250, 250, 250, 200)

        if i == 1 and alignment == 'left':
            d.multiline_text((width_song[k], height_song_top), text=song_str[f'col_{k}'], font=fnt, fill=color,
                             align='left', spacing=space_line)

        elif i == 1 and alignment == 'right':

            d.multiline_text((width_song[k], height_song_top), text=song_str[f'col_{k}'], font=fnt, fill=color,
                             align='left', spacing=space_line)

        else:
            d.multiline_text((width_song[k], height_song_top), text=song_str[f'col_{k}'], font=fnt, fill=color,
                             align='left', spacing=space_line)

    if show_img:
        print(width_song)


# Draw singer
    text_singer = ''
    _singer_color = color
    fnt = ImageFont.truetype(font_singer, _size_singer)
    # get a drawing content
    d = ImageDraw.Draw(txt)
    _offset_line = space_line - _height_singer

    if show_img:
        print(f"the number of song in one page {j}")

    for index in range(sum_song):
        text_singer += f"{list_singer[index]['name']}\n"

    _width_tmp, _height_tmp = d.textsize(text_singer, font=fnt)

    # _width_singer = width_song[0] - _width_tmp + 5

    if show_img:
        print(_width_singer)
        print(_width_tmp)

    spacing = _offset_line + _height_text

    d.multiline_text((width_song[0] + 5, height_song_top + _height_text + int(_offset_line/2)),
                     text=text_singer, font=fnt, fill=_singer_color, align="left", spacing=spacing)

    out = Image.alpha_composite(im, txt)
    if show_img:
        out.show()

    time = datetime.now()
    current_time = time.strftime("%H:%M:%S")
    current_date = time.date()

    path_new = f"{path_output}/{current_date}_{current_time}.png"

    try:
        out.save(path_new)
    except Exception as error:
        print(error)
        return False

    result = (path_new, sum_song)

    del out, time, current_time, current_date, fnt, im

    return result


if __name__ == '__main__':
    input_path = '../../../develop_env/images/background/background.jpg'
    path_font_title = '../../../develop_env/font3d/3Dumb.ttf'
    path_font_song = '../../../develop_env/font2d/True2D.otf'
    ob_path = '../../../develop_env/object'
    ob_list = os.listdir(ob_path)
    im_ob = f"{ob_path}/{ob_list[random.randint(0, len(ob_list)-1)]}"
    print(im_ob)
    im_ob = '../../../develop_env/object/stock-photo-292257879.jpg'

    try:
        with open('../../../develop_env/data/list_song.json') as json_file:
            js_txt = json.load(json_file)
            print(js_txt)
    except ValueError as error:
        print(error)
    black_zone = (0, 50)

    draw_list(im_ob, path_font_title, path_font_song, black_zone, js_txt, alignment='left')
