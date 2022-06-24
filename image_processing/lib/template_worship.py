
import face_recognition
import os
import io
import configparser
import numpy as np
import json
import logging

try:
    from .text_insert import draw_song, draw_template_symmetry, \
        draw_template_collum, draw_one_col_no_singer, draw_double_col, draw_one_col_singer
except:
    from text_insert import draw_song, draw_template_symmetry, \
        draw_template_collum, draw_one_col_no_singer, draw_double_col, draw_one_col_singer

try:
    from .object_segment import load_model, get_object, predict, \
        add_margin, change_location
except:
    from object_segment import load_model, get_object, predict, \
        add_margin, change_location

from PIL import Image, ImageDraw, ImageFilter, ImageChops

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


def get_txt_box(im, ob_region, debug=False):
    """

    :param im:
    :param ob_region:
    :param debug:
    :return:
    """

    if len(ob_region) != 4:
        print(f"{ob_region} format not True")
        return False

    gray = im.convert("L")
    bw = gray.point(lambda x: 0 if x < 5 else 255, '1')
    if debug:
        gray.show()
        bw.show()

    im_array = np.asarray(bw)
    max_i = 0
    max_j = 0
    min_i = im_array.shape[0]
    min_j = im_array.shape[1]
    off_set = 10
    for i in range(im_array.shape[0]):
        for j in range(im_array.shape[1]):
            if im_array[i][j] == 0:
                if (j > max(ob_region[0] + off_set, ob_region[2] + off_set)) or \
                        (j < min(ob_region[0] - off_set, ob_region[2] - off_set)):
                    if i > max_i:
                        max_i = i
                    elif i < min_i:
                        min_i = i
                    if j > max_j:
                        max_j = j
                    elif j < min_j:
                        min_j = j

    return (min_j, min_i, max_j, max_i)


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


def _detect_text_region(im_frame, im_text_tmp, debug=False):
    """

    :param im_frame:
    :param im_text_tmp:
    :param debug:
    :return:
    """
    new_im = ImageChops.difference(im_frame, im_text_tmp)
    gray = new_im.convert("L")
    mask = gray.point(lambda x: 0 if x < 30 else 255, '1')
    text_region = mask.getbbox()
    if debug:
        im_frame.show()
        im_text_tmp.show()
        new_im.show()
        gray.show()
        mask.show()
        logger.info(f"text region is {text_region}")
    return mask, text_region


def template_generation_worship(frame_template, img_txt,
                                path_out, collum_mode=1,
                                js_txt='', debug=False):
    """
    Detail:
    :param frame_template:
    :param img_txt:
    :param path_out:
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

    try:
        path_font = js_txt["path_font_song"]
    except Exception as error:
        result["content"] = error
        return result

    # Check conditional input
    if _check_img(frame_template) is False:
        result["image_false"] = frame_template
        result["content"] = 'image frame is wrong'
        return result

    if _check_img(img_txt) is False:
        result["image_false"] = img_txt
        result["content"] = 'image text is wrong'
        return result

    if _check_font(path_font) is False:
        result["content"] = f'Font {path_font} is wrong'
        return result
    if os.path.isdir(path_out) is False:
        logger.info(f"{path_out} was not found")
        result["content"] = f'Font {path_out} is wrong'
        return result

    if collum_mode not in [1, 2]:
        logger.info(logger.info(f"{collum_mode} have to 1 or 2"))
        result["content"] = f"{collum_mode} have to 1 or 2"
        return result

    # Open image frame
    _im_frame = Image.open(frame_template)

    if _im_frame.size != (W, H):
        _im_frame = _im_frame.resize((W, H))
        if debug:
            logger.info(f"_im_frame of size is {W, H}")

    im_frame = _im_frame.copy()
    if debug:
        im_frame.show()

    im_text = Image.open(img_txt)

    if im_text.size != (W, H):
        im_text = im_text.resize((W, H))

    _im_text, text_region = _detect_text_region(_im_frame, im_text, debug=debug)

    template = io.BytesIO()
    im_frame.save(template, format='png')
    try:
        if collum_mode == 1:
            try:
                mode = js_txt["mode"]
                if mode not in ["line", "no_line", "singer"]:
                    print(f"{js_txt['mode']} must have line or no_line or singer")
                    result["content"] = f"{js_txt['mode']} must have line or no_line"
                    return result

            except:
                mode = "singer"
                js_txt["mode"] = "singer"

            if mode == "singer":
                result = draw_one_col_no_singer(template, text_region=text_region,
                                                path_output=path_out, js_txt=js_txt, debug=debug)
            else:
                result = draw_one_col_singer(template,
                                             text_region=text_region,
                                             path_output=path_out, js_txt=js_txt,
                                             debug=debug)

        elif collum_mode == 2:
            result = draw_double_col(template, text_region=text_region,
                                     path_output=path_out, js_txt=js_txt,
                                     debug=debug)
        else:
            result["content"] = f"{collum_mode} have to 1 or 2"
            return result

        if result is False:
            result["content"] = "Can not draw text into image"
            return result

    except Exception as error:
        logger.info(error)
        result["content"] = f"{error}"
        return result

    if debug:
        logger.info(result)

    return result


if __name__ == "__main__":
    img_txt = "./develop_env/test_case/2021-06-15T18:18:15.625Z_DSA.jpg"
    frame_template = "./develop_env/test_case/2021-06-15T18:18:03.074Z_RFGDF.jpg"

    path_font = './develop_env/font2d/ACaslonPro-Bold.otf'
    path_out = "./develop_env/output"

    try:
        with open('./develop_env/data/list_song.json') as json_file:
            data = json.load(json_file)
            print(data)
    except ValueError as error:
        print(error)

    path = template_generation_worship(frame_template, img_txt, path_out,
                                       collum_mode=1, js_txt=data, debug=True)

    print(path)

