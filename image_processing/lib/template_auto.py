
import face_recognition
import os
import io
import configparser
import numpy as np
import json
import logging

from io import BytesIO

try:
    from .object_segment import load_model, get_object, add_margin
except:
    from object_segment import load_model, get_object, add_margin
try:
    from .text_insert import draw_list_style_1
except:
    from text_insert import draw_list_style_1


try:
    from .text_insert import draw_song, draw_template_symmetry, \
        draw_template_collum, draw_one_col_no_singer, draw_double_col, \
        draw_one_col_singer, draw_double_col_2_side
except:
    from text_insert import draw_song, draw_template_symmetry, \
        draw_template_collum, draw_one_col_no_singer, draw_double_col, \
        draw_one_col_singer, draw_double_col_2_side

try:
    from .object_segment import load_model, get_object, predict, \
        add_margin, change_location
except:
    from text_insert import draw_song, draw_template_symmetry, \
        draw_template_collum, draw_one_col_no_singer, draw_double_col, \
        draw_one_col_singer, draw_double_col_2_side


try:
    from background_change import change
except:
    from .background_change import change

from PIL import Image, ImageChops

try:
    from .adjust_img import crop_img
except:
    from adjust_img import crop_img


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
OFFSET_EDGE = int(details_dict['offset_edge'])


def _check_img(img):
    """
    Detail : to check image conditional
    :param img: path of image
    :return: True/False
    """
    if os.path.isfile(img) is False:
        logger.info(f"Can not find {img}")
        return False
    if img.lower().endswith(('.jpg', '.png', '.jpeg')) is False:
        logger.info(f"{img} format not True")
        return False
    return True


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


def _change_location(im, coordinate, size_img, show_orig=False):
    """

    :param im:
    :param coordinate: object region of coordinate
    :param size_img:
    :param show_orig:
    :return:
    """
    _coordinate = list(coordinate)
    # Get contribute of crop_img
    width_ob, height_ob = im.size
    width_region, height_region = _coordinate[2] - _coordinate[0], _coordinate[3] - _coordinate[1]

    # Check size of image background with size object
    if width_ob != width_region or height_ob != height_region:
        if height_region == H:
            height_region = H - 20

        # div = min(width_ob / width_region, height_ob / height_region)
        div = height_ob/height_region

        if div < 0.65:
            div = 0.65
            _height_ob = int(height_ob / div)

            if _height_ob < 650:
                return False

        width_ob = int(width_ob / div)
        height_ob = int(height_ob / div)

        if width_ob > 3 * W / 4:
            return False

    im = im.resize((width_ob, height_ob))

    # Calculate parm for add_margin function
    top = _coordinate[1] if height_ob == height_region else _coordinate[1] + height_region - height_ob

    bottom = size_img[1] - _coordinate[3]

    if coordinate[0] == 0:
        left = 0
        right = W - width_ob
    elif coordinate[2] > 2 * size_img[0] / 3:
        left = W - width_ob
        right = 0
    else:
        left = _coordinate[0] if width_ob == width_region else \
            _coordinate[0] + (width_region - width_ob) / 2

        right = size_img[0] - _coordinate[2] if width_ob == width_region else \
            size_img[0] - _coordinate[2] + width_region - width_ob - (width_region - width_ob) / 2

    color = (0, 0, 0)   # Define with black ground

    # Canvas_img to fit with background
    canvas_img = add_margin(im, top=top, right=right, bottom=bottom, left=left, color=color)

    if show_orig:
        canvas_img.show()

    del top, bottom, left, right, im

    return canvas_img


def auto(net, img_origin,
        img_background,
        path_out,
        ob_position,
        collum_mode=1,
        js_txt='', debug=False):
    """
    Detail:
    :param net:
    :param img_origin:
    :param img_background:
    :param path_out:
    :param ob_position:
    :param collum_mode:
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

    # Check conditional input
    if _check_img(img_origin) is False:
        result["content"] = f"{img_origin} is wrong"
        return result
    
    if _check_img(img_background) is False:
        result["content"] = f"{img_background} is wrong"
        return result

    try:
        path_font = js_txt["path_font_song"]

    except Exception as error:
        result["content"] = error
        return result

    if _check_font(path_font) is False:
        result["content"] = "font is wrong"
        return result

    # if _check_font(path_font_singer) is False:
    #     result["content"] = "font is wrong"
    #     return result

    if os.path.isdir(path_out) is False:
        logger.info(f"{path_out} was not found")
        result["content"] = f"{path_out} was not found"
        return result
    
    if ob_position not in ["left", "right"]:
        logger.info(f"{ob_position} format not True")
        result["content"] = f"{ob_position} format not True"
        return result
    
    if ob_position == "left":
        ob_tp_region = [0, 0, 630, 720]
        text_region = [630, 0, 1270, 720]
    elif ob_position == "right":
        ob_tp_region = [630, 0, 1280, 720]
        text_region = [10, 0, 630, 720]
    # elif ob_position == "center":
    #     ob_tp_region = [320, 0, 950, 720]
    #     text_region = [[10, 0, 300, 720], [970, 0, 1270, 720]]
    else:
        logger.info(f"{ob_position} format not True")
        result["content"] = f"{ob_position} format not True"
        return result
        
    # Open image frame
    _im_frame = Image.open(img_background)

    if _im_frame.size != (W, H):
        _im_frame = _im_frame.resize((W, H))
        if debug:
            logger.info(f"_im_frame of size is {W, H}")

    im_frame = _im_frame.copy()
    img_frame = BytesIO()
    im_frame.save(img_frame, format="PNG")

    if debug:
        im_frame.show()

    # process one of image in list
    
    # Open new object image input
    im_ori = Image.open(img_origin)
    im_ori = crop_img(net, im_ori, debug=debug)

    if debug:
        im_ori.show()
   
    # Check result
    if (ob_tp_region[2] - ob_tp_region[0] <= 0) or (ob_tp_region[3] - ob_tp_region[1] <= 0):
        logger.info(f"Object region is wrong")
        result["content"] = "Object region is wrong"
        return result

    # Calculator size of object in template
    _size_ob_tp_region = (ob_tp_region[2] - ob_tp_region[0],
                          ob_tp_region[3] - ob_tp_region[1])

    # # Predict object in the picture
    img_ori_tmp = BytesIO()

    _im_ori = crop_img(net, im_ori, debug=debug)
    _im_ori.save(img_ori_tmp, format="png")
    ob_position, old, im, _pred, _pred_blur = get_object(img_ori_tmp, net, show_img=debug, auto=True)

    if ob_position is False:
        logger.info("Object is not beautiful with this template")
        result["content"] = "Object is not beautiful with this template"
        result["image_false"] = img_origin
        return result

    elif ob_position == "left":
        ob_tp_region = [0, 0, 700, 720]
        text_region = [730, 0, 1270, 720]

    elif ob_position == "right":
        ob_tp_region = [580, 0, 1280, 720]
        text_region = [10, 0, 550, 720]

    _size_old = old.size

    if (_size_old[0] < _size_ob_tp_region[0] / 2.5) or (_size_old[1] < _size_ob_tp_region[1] / 2.5):
        logger.info("Object too small")
        result["content"] = "Object too small"
        result["image_false"] = img_origin
        return result

    _object_img = _change_location(old, coordinate=ob_tp_region, size_img=(W, H))

    if _object_img is False:
        logger.info("Object is not beautiful with this template")
        result["content"] = "Object is not beautiful with this template"
        result["image_false"] = img_origin
        return result

    _pred_img = _change_location(_pred, coordinate=ob_tp_region, size_img=(W, H),
                                 show_orig=debug)

    if _pred_img is False:
        logger.info("Object is not beautiful with this template")
        result["content"] = "Object is not beautiful (too small) with this template"
        result["image_false"] = img_origin

    _pred_blur = _change_location(_pred_blur, coordinate=ob_tp_region, size_img=(W, H))

    if debug:
        logger.info(_object_img.size)

    object_img = BytesIO()
    _object_img.save(object_img, format='png')

    _im_frame_tmp = change(object_img, img_frame, net, pred=_pred_img, pred_blur=_pred_blur,
                           save_status=False, blur=False, show_orig=debug)
    if debug:
        _im_frame_tmp.show()

    template = io.BytesIO()
    _im_frame_tmp.save(template, format='png')

    if collum_mode == 1:
        try:
            mode = js_txt["mode"]
            if mode not in ["line", "no_line", "singer"]:
                print(f"js_txt['mode'] must have line or no_line or singer")
                result["content"] = f"js_txt['mode'] must have line or no_line"
                return result

        except:
            mode = "singer"
            js_txt["mode"] = "singer"

        try:
            if mode != "singer":
                result = draw_one_col_singer(template, text_region=text_region, path_output=path_out, js_txt=js_txt,
                                             debug=debug)
            else:
                result = draw_one_col_no_singer(template, text_region=text_region, path_output=path_out, js_txt=js_txt,
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
        if ob_position == "center":
            try:
                result = draw_double_col_2_side(template, text_region=text_region,
                                                path_output=path_out, js_txt=js_txt,
                                                debug=debug)
            except Exception as error:
                logger.info(error)
                result["content"] = f"{error}"
                return result

        else:
            try:
                result = draw_double_col(template, text_region=text_region,
                                         path_output=path_out, js_txt=js_txt,
                                         debug=debug)

            except Exception as error:
                logger.info(error)
                result["content"] = f"{error}"
                return result
    elif collum_mode == "title_style":
        try:
            result = draw_list_style_1(template, text_region,
                                       path_output=path_out, js_txt=js_txt,
                                       debug=debug)
        except Exception as error:
            logger.info(error)
            result["content"] = f"{error}"
            return result

    if debug:
        logger.info(result)

    return result


if __name__ == "__main__":

    img_origin = "./develop_env/object/pexels-anna-tarazevich-4839770.jpg"

    img_background = "./develop_env/background/756d9d73c3c0957e6252c2855a5aec66.jpg"

    path_model = './model/u2net.pth'

    path_out = "./develop_env/output_test"

    try:
        with open('./develop_env/data/list_song.json') as json_file:
            data = json.load(json_file)
            print(data)
    except ValueError as error:
        print(error)
    net = load_model(path_model)

    result = auto(net, img_origin=img_origin, img_background=img_background,
                  path_out=path_out, ob_position="left", collum_mode=2,
                  js_txt=data, debug=True)
    logger.info(result)
    # im = Image.open(path)
    # im.show()
