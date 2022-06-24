"""""""""""""""""""""""
Author : NGUYEN DINH HAI
VER    : 1.0
DATE   : 2021, JAN 26
"""""""""""""""""""""""

import numpy as np
import os
import json
import random
import logging
import configparser

from io import BytesIO

from PIL import Image, ImageFilter, ImageOps

try:
    from .object_segment import load_model, get_object, predict, add_margin
except:
    from object_segment import load_model, get_object, predict, add_margin

try:
    from .text_insert import draw_double_col_2_side, draw_one_col_singer, draw_double_col, draw_one_col_no_singer
except:
    from text_insert import draw_double_col_2_side, draw_one_col_singer, draw_double_col, draw_one_col_no_singer


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
OFFSET_TEXT = int(details_dict["offset_text"])


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


def _get_text_region(ob_region):
    """
Detail:
    :param ob_region:
    :return:
    """

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

    return resp


# To make background to grayscale
def template_fl_image(net, path,
                      path_out,
                      collum_mode=1, outside=OFFSET_TEXT,
                      js_txt='', debug=False):

    """
    Detail:
    :param net:
    :param path:
    :param path_out:
    :param collum_mode:
    :param outside:
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

    # Check input
    if os.path.isfile(path) is False:
        print(f"{path} was not found")
        result["content"] = f"{path} was not found"
        return result
    if os.path.isdir(path_out) is False:
        print(f"{path_out} was not found")
        result["content"] = f"{path_out} was not found"
        return result

    im = Image.open(path)
    width, height = im.size

    if 2 > width / height > 1.4:
        pass
    else:
        result["content"] = 'Image size not compatible'
        return result

    im = _resize(im, width, height)

    width_im, height_im = im.size
    if width_im != W or height_im != H:
        result["content"] = "Can not resize fix follow define size"
        return result

    # gray = ImageOps.grayscale(im)
    # gray = gray.convert('RGB')

    if debug:
        im.show()
        # gray.show()

    old, pred = predict(net, np.array(im))
    pred = pred.resize(im.size, resample=Image.BILINEAR)  # remove resample
    _ob_region = pred.getbbox()

    try:
        _text_region = _get_text_region(_ob_region)
        _text_mode = _text_region["status"]
    except Exception as error:
        result["content"] = error
        return result

    _text_region_ = _text_region["region"]

    if _text_mode is False:
        result["content"] = "Can not detect text region"
        return result

    if debug:
        logger.info(_ob_region)

    if debug: pred.show()

    # new_img = Image.composite(im, gray, pred.convert("L"))

    # if debug: new_img.show()

    # template = BytesIO()
    # new_img.save(template, format='png')

    text_region = []

    if len(_text_region_) == 1:
        if len(_text_region_[0]) == 4:
            text_region = list(_text_region_[0])
            if _text_mode == "left":
                text_region[2] += outside
            elif _text_mode == "right":
                if text_region[0] >= outside:
                    text_region[0] = text_region[0] - outside
                else:
                    text_region[0] = 0

    elif len(_text_region_) == 2:
        try:
            result = draw_double_col_2_side(path, text_region=_text_region_,
                                            path_output=path_out, js_txt=js_txt,
                                            debug=debug)
            result["status"] = "success"
            return result
        except Exception as error:
            result["content"] = error
            return result

    else:
        result["content"] = "Text region format is wrong"
        return result

    if collum_mode == 1:
        try:
            mode = js_txt["mode"]
            if mode not in ["line", "no_line", "singer"]:
                print(f"js_txt['mode'] must have line or no_line or singer")
                result["content"] = f"js_txt['mode'] must have line or no_line"
                return result

        except:
            mode = "singer"
            # js_txt["mode"] = "singer"

        try:
            if mode != "singer":
                result = draw_one_col_singer(path, text_region=text_region, path_output=path_out, js_txt=js_txt,
                                             debug=debug)
            else:
                result = draw_one_col_no_singer(path, text_region=text_region, path_output=path_out, js_txt=js_txt,
                                                debug=debug)

            if debug:
                logger.info(result)

            if result is False:
                result["content"] = "Can not draw text into the picture"
                return result

        except Exception as error:
            logger.info(error)
            result["content"] = f"{error}"
            return result
    elif collum_mode == 2:
        if _text_region == "double":
            try:
                result = draw_double_col_2_side(path, text_region=text_region,
                                                path_output=path_out, js_txt=js_txt,
                                                debug=debug)
            except Exception as error:
                logger.info(error)
                result["content"] = f"{error}"
                return result

        else:
            try:
                result = draw_double_col(path, text_region=text_region,
                                         path_output=path_out, js_txt=js_txt,
                                         debug=debug)

            except Exception as error:
                logger.info(error)
                result["content"] = f"{error}"
                return result

    if debug:
        logger.info(result)

    del im, pred

    return result


if __name__ == '__main__':
    path_background = './develop_env/images/background/background.jpg'
    path_folder = './develop_env/images/task'
    path_font_title = './develop_env/font3d/3d-noise.ttf'
    path_font_song = './develop_env/font2d/J19D.ttf'
    path_output = './develop_env'

    list_ob = os.listdir(path_folder)
    path_ground = f"./develop_env/object/pexels-tuáº¥n-kiá»t-jr-1382726.jpg"
    print(path_ground)
    # path_ground = "../../develop_env/object/stock-photo-1019919200.jpg"
    data = dict()

    try:
        with open('./develop_env/data/list_song.json') as json_file:
            data = json.load(json_file)
            print(data)
    except ValueError as error:
        print(error)

    path_model = './model/u2net.pth'

    net = load_model(path_model, model_name='u2net')

    print(template_fl_image(net, path=path_ground, path_out=path_output, collum_mode=1, js_txt=data, debug=True))

