"""""""""""""""""""""""
Author : NGUYEN DINH HAI
VER    : 2.0
DATE   : 2021, Apr 26
"""""""""""""""""""""""

import face_recognition
import numpy as np
import os
import json
import configparser

from io import BytesIO
import random
import logging
# from random import random

from datetime import datetime

from PIL import Image, ImageFilter

try:
    from .object_segment import load_model, get_object, predict, add_margin
except:
    from object_segment import load_model, get_object, predict, add_margin

try:
    from .text_insert import draw_text_one_line, draw_list, draw_text_multi_line
except:
    from text_insert import draw_text_one_line, draw_list, draw_text_multi_line

try:
    from .text_insert import draw_song, draw_template_symmetry, \
        draw_template_collum, draw_one_col_no_singer, draw_double_col, draw_one_col_singer
except:
    from text_insert import draw_song, draw_template_symmetry, \
        draw_template_collum, draw_one_col_no_singer, draw_double_col, draw_one_col_singer


# Set logging to print status
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

# Load file config
config = configparser.RawConfigParser()

try:
    config.read('config.cfg')
    details_dict = dict(config.items('CONFIG_IMAGE'))
except:
    print("Run in test environment")
    print(os.path.isfile('../../config.cfg'))
    config.read('../../config.cfg')
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
MIN_TEXT_REGION = int(details_dict['min_text_region'])


def _check_font(font):
    """
    Detail: to check font conditional
    :param font: path of font
    :return: True/False
    """
    if os.path.isfile(font) is False:
        logger.info(f"{font} was not found")
        return False
    if font.lower().endswith(('ttf', 'otf')) is False:
        logger.info(f"{font} format not True")
        return False
    return True


def _get_ob_region(pred_im, debug=False):
    ob_box_region = pred_im.getbbox()

    if debug:
        new_im = pred_im.crop(ob_box_region)
        new_im.show()
        print(ob_box_region)

    return ob_box_region


def _get_text_region(ob_region):
    resp = dict()
    resp["status"] = ''
    text_region = []
    left = ob_region[0]
    top = ob_region[1]
    right = ob_region[2]
    bottom = ob_region[3]
    if left - WIDTH_OFFSET > MIN_TEXT_REGION:
        resp["status"] = "left"
        text_region.append((WIDTH_OFFSET, top, left, bottom))
    if W - WIDTH_OFFSET - right > MIN_TEXT_REGION:
        resp["status"] = "right"
        text_region.append((right, top, W - WIDTH_OFFSET, bottom))
    if len(text_region) == 0:
        resp["status"] = False
    elif len(text_region) == 2:
        resp["status"] = "double"
        resp["region"] = text_region
    else:
        resp["region"] = text_region

    return text_region


def _resize(im_ob, width, height, debug=False):
    """
    Detail :
    :param im_ob:
    :param width:
    :param height:
    :return:
    """
    div = max(H/height, W/width)
    width_new = int(width * div)
    height_new = int(height * div)
    im_ob = im_ob.resize((width_new, height_new))
    if debug:
        print(im_ob.size)
        im_ob.show()
        print(abs(W - width_new), abs(H - height_new), width_new, height_new)
    new_im = im_ob.crop((0, 0, W, H))

    del div, width_new, height_new, im_ob

    return new_im


# Background blurring
def blurring(img, net, path_output_folder, path_font_title, path_font_song, js_text, align="left",
             size_text=25, size_title=50, show_img=False):
    """

    :param img:
    :param net:
    :param path_output_folder:
    :param path_font_title:
    :param path_font_song:
    :param js_text:
    :param align:
    :param size_text:
    :param size_title:
    :param show_img:
    :return:
    """

    # To create new variable
    result = dict()
    result["status"] = "error"
    result["content"] = ''
    result["data"] = []
    result["image_false"] = ''

    # check input
    if os.path.isfile(img) is False:
        print(f"{img} was not found")
        result["content"] = f"{img} was not found"
        return result

    if os.path.isdir(path_output_folder) is False:
        print(f"{path_output_folder} was not found")
        result["content"] = f"{path_output_folder} was not found"
        return result

    try:
        path_font = js_text["path_font_song"]
        # path_font_singer = js_txt["path_font_singer"]
    except Exception as error:
        result["content"] = error
        return result

    if _check_font(path_font) is False:
        result["content"] = "font is wrong"
        return result

    im = Image.open(img)
    width, height = im.size
    im = _resize(im, width, height)

    width_im, height_im = im.size
    if width_im != W or height_im != H:
        result["content"] = "Can not resize fix to define size"
        return result

    # # Check face in origin image
    # image = face_recognition.load_image_file(im)
    # location = face_recognition.face_locations(image)
    # if len(location) == 0:
    #     result["content"] = "Can not find the face in the picture"
    #     return result

    if show_img:
        im.show()

    bg = im.copy()
    pred, pre_blur = predict(net, np.array(im))
    pred_blur = pre_blur.resize(im.size, resample=Image.BILINEAR)  # remove resample
    pred = pred.resize(im.size, resample=Image.BILINEAR)
    _ob_region = _get_ob_region(pred)
    _text_region = _get_text_region(_ob_region)
    _text_mode = _text_region["status"]

    if _text_mode is False:
        result["content"] = "Can not detect text region"
        return result

    if show_img: pred.show()

    background = bg.filter(ImageFilter.BLUR)

    new_img = Image.composite(im, background, pred_blur.convert("L"))

    if show_img: new_img.show()

    template = BytesIO()
    new_img.save(template, format='png')
    path_new = draw_list(template, path_font_title, path_font_song, black_zone=[], path_output=path_output_folder,
                         size_text=size_text, size_title=size_title,
                         js_txt=js_text, alignment=align, show_img=show_img)

    del im, bg, pred, new_img, template

    return path_new


if __name__ == '__main__':
    # img = '../../develop_env/images/ground/girl.png'
    path_model = '../../model/u2net.pth'
    # print(img.size)

    path_folder = './develop_env/images/bgremoval'
    path_font_title = './develop_env/font3d/3d-noise.ttf'
    path_font_song = './develop_env/font2d/J19D.ttf'
    path_output = "./develop_env"

    list_ob = os.listdir(path_folder)
    path_ground = f"{path_folder}/{list_ob[random.randint(0, len(list_ob) - 1)]}"
    print(path_ground)
    data = {}

    path_ground = "./develop_env/object/pexels-tuáº¥n-kiá»t-jr-1382726.jpg"

    try:
        with open('./develop_env/data/list_song.json') as json_file:
            data = json.load(json_file)
            print(data)
    except ValueError as error:
        print(error)

    path_model = './image_processing/lib/object_segment/u2net.pth'

    net = load_model(path_model, model_name='u2net')
    print(blurring(path_ground, net,
                   path_output_folder=path_output,
                   path_font_title=path_font_title,
                   path_font_song=path_font_song,
                   size_text=30,
                   size_title=50,
                   js_text=data,
                   show_img=True)
          )