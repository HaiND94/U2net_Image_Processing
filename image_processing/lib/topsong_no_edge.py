
import face_recognition
import os
import io
import configparser
import numpy as np
import json
import logging

from io import BytesIO

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

try:
    from background_change import change
except:
    from .background_change import change

from PIL import Image, ImageChops, ImageOps
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


def get_ob_box_multi(im, debug=False):
    """

    :param im: im of picture contain object
    :param debug: to debud show status
    :return: the region of object
    """

    _ob_box = im.getbbox()

    if _ob_box[0] < 80:
        _ob_location = 'left'
    elif _ob_box[2] > 1150:
        _ob_location = 'right'
    else:
        _ob_location = 'center'

    return _ob_box, _ob_location


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


def _detect_ob_region(im_frame, im_ob_tmp, debug=False):
    """

    :param im_frame:
    :param im_ob_tmp:
    :param debug:
    :return:
    """

    new_im = ImageChops.difference(im_frame, im_ob_tmp)
    if debug:
        new_im.show()
    gray = new_im.convert("L")
    if debug:
        gray.show()
    ob_region = gray.point(lambda x: 255 if x > 25 else 0, '1')
    mask = gray.point(lambda x: 0 if x > 25 else 255, '1')
    if debug:
        ob_region.show()
        mask.show()
    return ob_region, mask


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


def _detect_text_region(im_frame, im_text_tmp, debug=False):
    """

    :param im_frame:
    :param im_text_tmp:
    :param debug:
    :return:
    """
    new_im = ImageChops.difference(im_frame, im_text_tmp)
    gray = new_im.convert("L")
    mask = gray.point(lambda x: 0 if x < 25 else 255, '1')
    text_region = mask.getbbox()
    if debug:
        im_frame.show()
        im_text_tmp.show()
        new_im.show()
        gray.show()
        mask.show()
        logger.info(f"text region is {text_region}")
    return mask, text_region


def _change_location(im, coordinate, size_img, show_orig=False, ob_location='center', top_status=False):
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
    _height_region = height_region

    # Check size of image background with size object
    if width_ob != width_region or height_ob != height_region:
        div_w = width_ob / width_region
        div_h = height_ob / height_region
        div = max(div_w, div_h)
        if height_region == H and div > 1 and top_status:
            print("Image object not beautiful")
            return False

        width_ob = int(width_ob / div)
        height_ob = int(height_ob / div)

        if width_ob > width_region:
            print("Image object not beautiful")
            return False

        # if width_ob > 2 * W / 3:
        #     return False

    im = im.resize((width_ob, height_ob))

    # print(f"_coordinate is {_coordinate}")

    # Calculate parm for add_margin function
    if ob_location == 'left':
        left = 0
        right = size_img[0] - _coordinate[2]
    elif ob_location == 'right':
        left = _coordinate[0]
        right = 0
    else:
        left = _coordinate[0] if width_ob == width_region else _coordinate[0] + int((width_region - width_ob) / 2)
        right = size_img[0] - _coordinate[2] if width_ob == width_region else \
            size_img[0] - _coordinate[2] + width_region - width_ob - int((width_region - width_ob) / 2)

    top = _coordinate[1] if height_ob == _height_region else _coordinate[1] + _height_region - height_ob
    bottom = size_img[1] - _coordinate[3]
    color = (0, 0, 0)   # Define with black ground

    # Canvas_img to fit with background
    canvas_img = add_margin(im, top=top, right=right, bottom=bottom, left=left, color=color)

    if show_orig:
        canvas_img.show()

    del top, bottom, left, right, im

    return canvas_img


def top_songs_no_edge(net, list_img_origin, frame_template,
                      list_img_ob, img_txt,
                      path_out,
                      collum_mode=1,
                      js_txt='', debug=False):
    """

    :param net:
    :param list_img_origin:
    :param frame_template:
    :param list_img_ob:
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

    try:
        path_font = js_txt["path_font_song"]
        # path_font_singer = js_txt["path_font_singer"]
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

    # Open image frame
    _im_frame = Image.open(frame_template)

    if _im_frame.size != (W, H):
        _im_frame = _im_frame.resize((W, H))
        if debug:
            logger.info(f"_im_frame of size is {W, H}")

    im_frame = _im_frame.copy()
    img_frame = BytesIO()
    im_frame.save(img_frame, format="PNG")

    _im_frame_tmp = False

    if debug:
        im_frame.show()

    # process one of image in list
    for index, img_ori in enumerate(list_img_origin):
        # Open new object image input
        im_ori = Image.open(img_ori)
        # Check face in origin image
        # image = face_recognition.load_image_file(im_ori)
        # location = face_recognition.face_locations(image)
        # if len(location) != 1:
        #     logger.info(f"Face region was not found at {img_ori}")
        #     result["content"] = f"Face region was not found at {img_ori}"
        #     result["image_false"] = img_ori
        #     return result

        # Open object image template input
        im_ob_tp = Image.open(list_img_ob[index])

        # Check size of object image template
        if im_ob_tp.size != (W, H):
            im_ob_tp = im_ob_tp.resize((W, H))

        if debug:
            # im_ori.show()
            im_ob_tp.show()

        # Get object position in template
        _im_ob_tp, mask = _detect_ob_region(_im_frame, im_ob_tp, debug=debug)
        if debug:
            _im_ob_tp.show()
            mask.show()
        ob_tp_region, ob_location = get_ob_box_multi(_im_ob_tp, debug=debug)
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
            # im_ori.show()
            im_ob_tp.show()
            print(f"ob_tp_region is {ob_tp_region}")

        # Calculator size of object in template
        _size_ob_tp_region = (ob_tp_region[2] - ob_tp_region[0],
                              ob_tp_region[3] - ob_tp_region[1])

        # # Predict object in the picture
        img_ori_tmp = BytesIO()
        _im_ori = crop_img(net, im_ori, debug=debug)
        _im_ori.save(img_ori_tmp, format="png")
        ob_img_location, top_status, old, im, _pred, _pred_blur = get_object(img_ori_tmp, net,
                                                                             show_img=debug, top_song=True)

        if ob_img_location == 'center' or ob_img_location == ob_location:
            pass
        elif (ob_img_location == 'right' and ob_location == 'left') or\
             (ob_img_location == 'left' and ob_location == 'right'):
            old = ImageOps.mirror(old)
            im = ImageOps.mirror(im)
            _pred = ImageOps.mirror(_pred)
            _pred_blur = ImageOps.mirror(_pred_blur)
        else:
            logger.info("This object location not beautiful with template")
            result["content"] = "This object location not beautiful with this template"
            result["image_false"] = img_ori
            return result

        _size_old = old.size

        if (_size_old[0] < _size_ob_tp_region[0] / 1.8) or (_size_old[1] < _size_ob_tp_region[1] / 1.8):
            logger.info("Object too small")
            result["content"] = "Object too small"
            result["image_false"] = img_ori
            return result

        # ob_img_location = "right"

        _object_img = _change_location(old, coordinate=ob_tp_region, size_img=(W, H),
                                       show_orig=debug, ob_location=ob_img_location, top_status=top_status)
        if _object_img is False:
            logger.info("Object is not beautiful with this template")
            result["content"] = "Object is not beautiful with this template"
            result["image_false"] = img_ori
            return result

        _pred_img = _change_location(_pred, coordinate=ob_tp_region, size_img=(W, H),
                                     show_orig=debug, ob_location=ob_img_location, top_status=top_status)
        _pred_blur = _change_location(_pred_blur, coordinate=ob_tp_region, size_img=(W, H),
                                      show_orig=debug, ob_location=ob_img_location, top_status=top_status)
        if debug:
            logger.info(_object_img.size)

        object_img = BytesIO()
        _object_img.save(object_img, format='png')

        _im_frame_tmp = change(object_img, img_frame, net, pred=_pred_img, pred_blur=_pred_blur,
                               save_status=False, blur=False, show_orig=debug)

        object_img = BytesIO()
        _im_frame_tmp.save(object_img, format='png')

        _im_frame_tmp = change(img_frame, object_img, net, pred=_pred_img, pred_blur=_pred_blur,
                               save_status=False, blur=False,mask=mask, show_orig=debug)

        if debug:
            _im_frame_tmp.show()

    # Draw text into the picture
    im_text = Image.open(img_txt)

    if im_text.size != (W, H):
        im_text = im_text.resize((W, H))

    _im_text, text_region = _detect_text_region(_im_frame, im_text, debug=debug)
    # text_region = get_ob_box_multi(_im_text, debug=debug)

    # Check _im_frame_tmp variable
    if _im_frame_tmp is False:
        logger.info("Template design is not True")
        result["content"] = "Template design is not True"
        return result

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
        try:
            result = draw_double_col(template, text_region=text_region,
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

    # list_img_origin = ["./develop_env/object/pexels-ali-pazani-2681751.jpg"]
    list_img_origin = ["./develop_env/object/pexels-ali-pazani-2887718.jpg"]
    list_img_ob = ["./develop_env/ex1/ob.jpg"]
    img_txt = "./develop_env/ex1/text.jpg"
    frame_template = "./develop_env/ex1/frame.jpg"

    path_model = './model/u2net.pth'

    # path_font = './develop_env/font2d/ACaslonPro-Bold.otf'
    # path_font_singer = "./develop_env/font2d/AGaramondPro-Italic.otf"

    path_out = "./develop_env/output_test"

    try:
        with open('./develop_env/data/list_song.json') as json_file:
            data = json.load(json_file)
            print(data)
    except ValueError as error:
        print(error)
    net = load_model(path_model)

    result = top_songs_no_edge(net, list_img_origin, frame_template,
                               list_img_ob, img_txt, path_out,
                               js_txt=data, debug=True)
    logger.info(result)
    # im = Image.open(path)
    # im.show()
