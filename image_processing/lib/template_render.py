
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

try:
    from .adjust_img import crop_img
except:
    from adjust_img import crop_img

try:
    from .topsong_no_edge import _detect_ob_region, get_ob_box_multi, _detect_text_region
except:
    from topsong_no_edge import _detect_ob_region, get_ob_box_multi, _detect_text_region


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


def fit_ob(im_ob, size):
    """

    :param im_ob:
    :param size:
    :return:
    """
    size_ob = im_ob.size
    div = min(size_ob[0] / size[0], size_ob[1] / size[1])
    new_size = (int(size_ob[0] / div), int(size_ob[1] / div))
    _new_im = im_ob.resize(new_size)
    result_im = _new_im.crop((0, 0, size[0], size[1]))

    return result_im


def get_ob_box_singer(im, debug=False):
    """

    :param im: im of picture contain object
    :param debug: to debud show status
    :return: the region of object
    """

    bw = im.point(lambda x: 0 if x < 2 else 255, '1')
    if debug:
        im.show()
        bw.show()
    im_array = np.asarray(bw)
    max_i = 0
    max_j = 0
    min_i = im_array.shape[0]
    min_j = im_array.shape[1]
    for i in range(im_array.shape[0]):
        for j in range(im_array.shape[1]):
            if im_array[i][j] == 0:
                if i > max_i:
                    max_i = i
                elif i < min_i:
                    min_i = i
                if j > max_j:
                    max_j = j
                elif j < min_j:
                    min_j = j

    return (min_j, min_i, max_j, max_i)


def get_ob_box(im, debug=False):
    """

    :param im: im of picture contain object
    :param debug: to debud show status
    :return: the region of object
    """

    gray = im.convert("L")
    bw = gray.point(lambda x: 0 if x < 2 else 255, '1')
    if debug:
        gray.show()
        bw.show()
    im_array = np.asarray(bw)
    max_i = 0
    max_j = 0
    min_i = im_array.shape[0]
    min_j = im_array.shape[1]
    for i in range(im_array.shape[0]):
        for j in range(im_array.shape[1]):
            if im_array[i][j] == 0:
                if i > max_i:
                    max_i = i
                elif i < min_i:
                    min_i = i
                if j > max_j:
                    max_j = j
                elif j < min_j:
                    min_j = j

    # print(min_j, min_i, max_j, max_i)
    return (min_j, min_i, max_j, max_i)


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


def template_generation(net, img_origin,
                        img_ob, img_txt,
                        path_font, path_font_singer, path_out,
                        size_text=25, js_txt='', debug=False):
    """

    :param net:
    :param img_origin:
    :param img_ob:
    :param img_txt:
    :param path_font:
    :param path_font_singer:
    :param path_out:
    :param size_text:
    :param js_txt:
    :param debug:
    :return:
    """

    if (os.path.isfile(img_ob) is False) or (os.path.isfile(img_txt) is False) or\
            (os.path.isfile(img_origin) is False):
        logger.info("file was not found")
        return False

    if (img_ob.lower().endswith(('.jpg', '.png', '.jpeg')) is False) or\
       (img_txt.lower().endswith(('.jpg', '.png', '.jpeg')) is False) or\
       (img_origin.lower().endswith(('.jpg', '.png', '.jpeg')) is False):
        logger.info("input image format is not True")
        return False

    if os.path.isfile(path_font) is False:
        logger.info(f"{path_font} was not found")
        return False

    if path_font.lower().endswith(('.tff', 'off')):
        logger.info(f"{path_font} format not True")
        return False

    if os.path.isdir(path_out) is False:
        logger.info(f"{path_font} was not found")
        return False

    im_ob = Image.open(img_ob)
    im_text = Image.open(img_txt)
    im_ori = Image.open(img_origin)

    # if debug is False:
    #     if im_ob.size != (W, H) or im_text.size != (W, H):
    #         logger.info(f"warring size of image must be {W}x{H}")
    #         return False

    if im_ob.size != (W, H) or im_text.size != (W, H):
        im_ob = im_ob.resize((W, H))
        im_text = im_text.resize((W, H))

    ob_region = get_ob_box(im_ob, debug=debug)
    text_region = get_txt_box(im_text, ob_region, debug=debug)

    if (ob_region[2] - ob_region[0] <= 0) or (ob_region[3] - ob_region[1] <= 0):
        logger.info(f"Object was not found at {img_ob}")
        return False

    if debug:
        im_ori.show()
        im_text.show()
        im_ob.show()
        print(f"ob_region is {ob_region}")
        print(f"text_region is {text_region}")

    _size_ob_region = (ob_region[2] - ob_region[0], ob_region[3] - ob_region[1])

    im_ori = crop_img(net, im_ori, debug=debug)

    pred, pre_blur = predict(net, np.array(im_ori))
    pred = pred.resize(im_ori.size, resample=Image.BILINEAR)  # remove resample
    _ob_box = pred.getbbox()
    _ob_crop = im_ori.crop(_ob_box)

    if debug:
        pred.show()
        _ob_crop.show()

    # _face_im = face_recognition.load_image_file(_ob_crop)
    # try:
    #     _face_location = face_recognition.face_locations(_face_im)
    # except Exception as erro:
    #     logger.info(erro)
    #     return False
    #
    # if len(_face_location) != 0:
    #     print(f"Face was not found in the picture {img_origin}")
    #     return False

    # _new_ob_origin = _ob_crop.resize(_size_ob_region)
    _new_ob_origin = fit_ob(_ob_crop, _size_ob_region)
    _left = ob_region[0]
    _right = W - ob_region[2]
    _top = ob_region[1]
    _bottom = H - ob_region[3]
    new_ob_origin = add_margin(pil_img=_new_ob_origin, color=(0, 0, 0),
                               top=_top, right=_right, left=_left, bottom=_bottom)

    gray = im_ob.convert("L")
    mask = gray.point(lambda x: 0 if x < 15 else 255, '1')
    new_img = Image.composite(im_ob, new_ob_origin, mask=mask)

    if debug:
        new_img.show()

    if debug:
        img = Image.new('RGB', (W, H), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.polygon(((text_region[0], text_region[1]), (text_region[2], text_region[1]),
                      (text_region[2], text_region[3]),
                      (text_region[0], text_region[3])), fill=(0, 0, 0))
        bg = im_ob.copy()
        bg = bg.filter(ImageFilter.GaussianBlur(10))
        bg.show()
        new_img = Image.composite(new_img, bg, img.convert("L"))
        new_img.show()

    template = io.BytesIO()
    new_img.save(template, format='png')
    path = draw_template_symmetry(template, path_font_song=path_font,
                                  path_font_singer=path_font_singer,
                                  text_region=text_region,
                                  path_output=path_out, js_txt=js_txt, size_txt=size_text,
                                  show_img=debug)
    if debug:
        logger.info(path)

    return path


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


# Calculator area of face region
def _face_attribute(face_location):
    if len(face_location) == 0 or False:
        print("Face not found")
        return False
    try:
        face_center_width = int((face_location[0][1] + face_location[0][3])/2)
        face_center_height = int((face_location[0][0]+face_location[0][2])/2)
        s = (face_location[0][2] - face_location[0][0]) * (face_location[0][3] - face_location[0][1])
    except Exception as error:
        print(error)
        return False

    return abs(s), face_center_width, face_center_height


def _fit_face_into_mold(size_mold, im, debug=False):
    """
    Detail : this function to fit ob to molde, and arange face into the mold
    :param size_mold: size of box
    :param im: im object of origin image
    :return: False or new_img
    """

    size_of_origin = im.size
    if size_of_origin[0] < 0.8 * size_mold[0] or size_of_origin[1] < 0.8 * size_mold[1]:
        logger.info("Image size to small")
        return False

    # Check face in origin image
    image = face_recognition.load_image_file(im)
    location = face_recognition.face_locations(image)
    if len(location) != 1:
        return False

    s, face_center_width, face_center_height = _face_attribute(location)

    _rate = 1
    _status = False
    new_size = (0, 0)
    while s > 0.2 * size_mold[0] * size_mold[1]:
        _status = True
        _rate -= 0.1
        if debug:
            logger.info(_rate)
        if _rate < 0:
            return False
        new_size = (int(_rate * size_of_origin[0]), int(_rate * size_of_origin[1]))
        _im = im.resize(new_size)
        # Check face in origin image
        image = face_recognition.load_image_file(_im)
        location = face_recognition.face_locations(image)
        if len(location) == 0:
            return False
        s, face_center_width, face_center_height = _face_attribute(location)
    if _status:
        im = im.resize(new_size)

    size_of_origin = im.size
    if size_of_origin[0] < size_mold[0] or size_of_origin[1] < size_mold[1]:
        _rate = 1.5 * max(size_mold[0] / size_of_origin[0], size_mold[1] / size_of_origin[1])
        new_size = (int(size_of_origin[0] * _rate) + 1, int(size_of_origin[1] * _rate) + 1)
        im = im.resize(new_size)
        size_of_origin = new_size
        image = face_recognition.load_image_file(im)
        location = face_recognition.face_locations(image)
        if len(location) == 0:
            return False
        s, face_center_width, face_center_height = _face_attribute(location)

    if debug:
        logger.info(_rate)
        logger.info(size_of_origin)
        logger.info(f"face attribute is {face_center_width}, {face_center_height}")
        logger.info(size_mold)

    # if (0.5 * size_mold[0]) < face_center_width < (size_of_origin[0] - 0.5 * size_mold[0]):
    #     left = face_center_width - int(0.5 * size_mold[0])
    #     right = left + size_mold[0]
    # else:
    #     logger.info("The width of origin image too small")
    #     return False
    #
    # if (0.5 * size_mold[1]) < face_center_height < (size_of_origin[1] - 0.5 * size_mold[1]):
    #     top = face_center_height - int(0.35 * size_mold[1])
    #     bottom = top + size_mold[1]
    # else:
    #     logger.info("The height of origin image too small")
    #     return False
    left = 0 if (0.5 * size_mold[0]) > face_center_width else face_center_width - int(0.5 * size_mold[0])
    if left != 0:
        if face_center_width < (size_of_origin[0] - 0.5 * size_mold[0]):
            right = left + size_mold[0]

        else:
            if size_of_origin[0] < size_mold[0]:
                logger.info("The width of origin image too small")
                return False
            else:
                right = size_of_origin[0]
                left = size_of_origin[0] - size_mold[0]

    elif left == 0:
        if size_of_origin[0] < size_mold[0]:
            logger.info("The width of origin image too small")
            return False
        else:
            right = left + size_mold[0]

    # check fix object of origin image into box of object
    top = 0 if (0.5 * size_mold[1]) > face_center_height else face_center_height - int(0.5 * size_mold[1])
    if top != 0:
        if face_center_height < (size_of_origin[1] - 0.5 * size_mold[1]):
            bottom = top + size_mold[1]
        elif size_of_origin[1] >= size_mold[1]:
            bottom = size_of_origin[1]
            top = size_of_origin[1] - size_mold[1]
        else:
            logger.info("The height of origin image too small")
            return False

    else:
        if size_of_origin[1] < size_mold[1]:
            logger.info("The height of origin image too small")
            return False
        else:
            bottom = size_mold[1]

    new_origin = im.crop((left, top, right, bottom))

    if debug:
        logger.info(f"left: {left}, top: {top}, right: {right}, bottom: {bottom}")
        new_origin.show()

    return new_origin


def template_generation_multi(net, list_img_origin, frame_template,
                              list_img_ob, img_txt,
                              path_out, collum_mode=1,
                              js_txt='', debug=False):

    # To create new variable
    result = dict()
    result["status"] = "error"
    result["content"] = ''
    result["data"] = []
    result["image_false"] = ''

    try:
        path_font = js_txt["path_font_song"]
        path_font_singer = js_txt["path_font_singer"]
    except Exception as error:
        result["content"] = error
        return result

    # Check conditional input
    if (len(list_img_origin) < 1) or (len(list_img_ob) < 1):
        logger.info("input not true")
        result["content"] = "image input not true"
        return result

    if len(list_img_origin) != len(list_img_ob):
        logger.info("the number of object origin or the number of object template not True")
        result["content"] = "the number of object origin or the number of object template not True"
        return result

    if _check_img(frame_template) is False:
        result["content"] = "frame image is wrong"
        return result
    if _check_img(img_txt) is False:
        result["content"] = "text image is wrong"
        return result
    for index, img in enumerate(list_img_ob):
        if _check_img(img) is False:
            result["content"] = "object image is wrong"
            return result

        if _check_img(list_img_origin[index]) is False:
            result["content"] = "origin image is wrong"
            result["image_false"] = list_img_origin[index]
            return result

    if _check_font(path_font) is False:
        result["content"] = "font is wrong"
        return result

    if _check_font(path_font_singer) is False:
        result["content"] = "font is wrong"
        return result

    if os.path.isdir(path_out) is False:
        logger.info(f"{path_out} was not found")
        result["content"] = f"{path_out} was not found"
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

    # process one of image in list
    for index, img_ori in enumerate(list_img_origin):
        # Open new object image input
        im_ori = Image.open(img_ori)
        im_ori = crop_img(net, im_ori, debug=debug)

        pred, pre_blur = predict(net, np.array(im_ori))
        pred = pred.resize(im_ori.size, resample=Image.BILINEAR)  # remove resample

        _ob_box = pred.getbbox()
        im_ori = im_ori.crop(_ob_box)

        # Open object image template input
        im_ob_tp = Image.open(list_img_ob[index])

        # Check size of object image template
        if im_ob_tp.size != (W, H):
            im_ob_tp = im_ob_tp.resize((W, H))

        if debug:
            im_ori.show()
            im_ob_tp.show()

        # Get object position in template
        _im_ob_tp, mask = _detect_ob_region(_im_frame, im_ob_tp, debug=debug)
        if debug:
            _im_ob_tp.show()
        ob_tp_region = get_ob_box_multi(_im_ob_tp, debug=debug)
        if debug:
            logger.info(ob_tp_region)

        # Check result
        if (ob_tp_region[2] - ob_tp_region[0] <= 0) or (ob_tp_region[3] - ob_tp_region[1] <= 0):
            logger.info(f"Object region was not found at {list_img_ob[index]}")
            result["content"] = f"Object region was not found at {list_img_ob[index]}"
            result["image_false"] = list_img_ob[index]
            return result

        # For debug built
        if debug:
            im_ori.show()
            im_ob_tp.show()
            print(f"ob_tp_region is {ob_tp_region}")

        # Calculator size of object in template
        _size_ob_tp_region = (ob_tp_region[2] - ob_tp_region[0],
                              ob_tp_region[3] - ob_tp_region[1])

        # # Predict object in the picture
        # pred, pre_blur = predict(net, np.array(im_ori))
        # pred = pred.resize(im_ori.size, resample=Image.BILINEAR)  # remove resample
        # _ob_box = pred.getbbox()
        # _ob_crop = im_ori.crop(_ob_box)

        # if debug:
        #     # pred.show()
        #     _ob_crop.show()

        _new_ob_origin = _fit_face_into_mold(_size_ob_tp_region, im_ori, debug=debug)
        # if _new_ob_origin is False and len(list_img_origin) == 1:
        #     # Predict object in the picture
        #     pred, pre_blur = predict(net, np.array(im_ori))
        #     pred = pred.resize(im_ori.size, resample=Image.BILINEAR)  # remove resample
        #     _ob_box = pred.getbbox()
        #     _ob_crop = im_ori.crop(_ob_box)
        #     _size_ob = _ob_crop.size
        #     _rate = max(_size_ob_tp_region[0]/_size_ob[0], _size_ob_tp_region[1]/_size_ob[1])
        #     _new_size = (int(_size_ob[0] * _rate), int(_size_ob[1] * _rate))
        #     _ob_crop = _ob_crop.resize(_new_size)
        #     if debug:
        #         _ob_crop.show()
        #     _size_ob = _ob_crop.size
        #
        #     # Get new value to crop origin object image use for aligment center
        #     _top = 0
        #     _bottom = _size_ob_tp_region[1]
        #     _left = int(abs(_size_ob[0] - _size_ob_tp_region[0])/2)
        #     _right = _left + _size_ob_tp_region[0]
        #
        #     # Crop image origin to fix size
        #     _new_ob_origin = _ob_crop.crop((_left, _top, _right, _bottom))
        #
        #     # if debug:
        #     #     _new_ob_origin.show()
        #
        # elif _new_ob_origin is False and len(list_img_origin) != 1:
        #
        #     return False
        if _new_ob_origin is False:
            result["content"] = f"Can not fix face in to image object"
            result["image_false"] = img_ori
            return result

        _left = ob_tp_region[0]
        _right = W - ob_tp_region[2]
        _top = ob_tp_region[1]
        _bottom = H - ob_tp_region[3]
        new_ob_origin = add_margin(pil_img=_new_ob_origin, color=(0, 0, 0),
                                   top=_top, right=_right, left=_left, bottom=_bottom)
        if debug:
            new_ob_origin.show()

        mask = mask.convert("L").filter(ImageFilter.GaussianBlur(1))

        im_frame = Image.composite(im_frame, new_ob_origin, mask=mask)

        if debug:
            logger.info(f"mask of size is {mask.size}")
            logger.info(f"new_ob_origin of size is {new_ob_origin.size}")
            logger.info(f"im_frame of size is {im_frame.size}")

        if debug:
            im_frame.show()

    im_text = Image.open(img_txt)

    if im_text.size != (W, H):
        im_text = im_text.resize((W, H))

    _im_text, text_region = _detect_text_region(_im_frame, im_text, debug=debug)
    # text_region = get_ob_box_multi(_im_text, debug=debug)

    template = io.BytesIO()
    im_frame.save(template, format='png')

    try:
        # path = draw_template_symmetry(template, path_font_song=path_font,
        #                               path_font_singer=path_font_singer,
        #                               text_region=text_region,
        #                               path_output=path_out, js_txt=js_txt, size_txt=size_text,
        #                               show_img=debug)
        if collum_mode == 1:
            try:
                mode = js_txt["mode"]
                if mode not in ["line", "no_line", "singer"]:
                    print(f"js_txt['mode'] must have line or no_line or singer")
                    result["content"] = f"js_txt['mode'] have to line or no_line"
                    return result

            except:
                mode = "singer"
                js_txt["mode"] = "singer"

            if mode != "singer":
                result = draw_one_col_singer(template,
                                             text_region=text_region,
                                             path_output=path_out, js_txt=js_txt,
                                             debug=debug)
            else:
                result = draw_one_col_no_singer(template, text_region=text_region,
                                                path_output=path_out, js_txt=js_txt,
                                                debug=debug)

        elif collum_mode == 2:
            result = draw_double_col(template, text_region=text_region,
                                     path_output=path_out, js_txt=js_txt,
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

    if debug:
        logger.info(result)

    return result


if __name__ == "__main__":
    im_ob = "./develop_env/template_render/template.jpg"
    im_ob = "./develop_env/template_render/ex4/09copy.png"

    im_text = "./develop_env/template_render/01.png"
    im_text = "./develop_env/template_render/multi_ob/text.jpg"

    list_img_origin = ["./develop_env/object/pexels-ali-pazani-2887718.jpg"]
    # list_img_origin = ["./develop_env/object/kyle-smith-tlowJ-oYAjU-unsplash.jpg",
    #                    "./develop_env/object/pexels-ali-pazani-2681751.jpg"]

    list_img_ob = ["develop_env/ex1/ob.jpg"]

    img_txt = "./develop_env/ex1/text.jpg"

    frame_template = "./develop_env/ex1/frame.jpg"
    path_model = './model/u2net_human_seg.pth'
    path_font = './develop_env/font2d/ACaslonPro-Bold.otf'
    path_font_singer = "./develop_env/font2d/AGaramondPro-Italic.otf"
    # path_out = "./develop_env"
    # list_img_origin = ["./develop_env/object/pexels-ali-pazani-2887718.jpg"]
    #
    # list_img_ob = ["./develop_env/template_render/ex9/ob.png"]
    # img_txt = "./develop_env/template_render/ex9/text.png"
    # frame_template = "./develop_env/template_render/ex9/frame.png"
    #
    # path_model = './image_processing/lib/object_segment/u2net_human_seg.pth'
    # path_font = './develop_env/font2d/ACaslonPro-Bold.otf'
    # path_font_singer = "./develop_env/font2d/AGaramondPro-Italic.otf"
    path_out = "./develop_env/output"

    try:
        with open('./develop_env/data/list_song.json') as json_file:
            data = json.load(json_file)
            print(data)
    except ValueError as error:
        print(error)
    net = load_model(path_model)

    # template_generation(net=net, img_origin=im_origin, img_ob=im_ob, path_out=path_out, size_text=25,
    #                     img_txt=im_text, js_txt=data, path_font=path_font,
    #                     path_font_singer=path_font_singer, debug=True)

    path = template_generation_multi(net, list_img_origin, frame_template,
                                     list_img_ob, img_txt,
                                     path_out, js_txt=data, debug=True)
    # im = Image.open(path)
    # im.show()
