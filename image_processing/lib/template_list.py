import os
import configparser
import json
import random

import face_recognition

try:
    from .text_insert import draw_list
except:
    from text_insert import draw_list

try:
    from .object_segment import load_model, get_object, predict, add_margin, change_location
except:
    from object_segment import load_model, get_object, predict, add_margin, change_location

try:
    from background_change import change
except:
    from .background_change import change

from io import BytesIO

from PIL import Image, ImageFilter

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


# Get width max face location
def width_face(face_locations):
    """

    :param face_locations:
    :return:
    """
    max_width = 0
    min_width = W
    for face_location in face_locations:
        max_width = max(face_location[3], face_location[1]) if max(face_location[3], face_location[1]) > max_width \
            else max_width
        min_width = min(face_location[3], face_location[1]) if min(face_location[3], face_location[1]) < min_width \
            else min_width
    return max_width, min_width


def template_list(img, bg, net, path_output, path_font_title, path_font_song, js_txt,
                  align='left', blur=True, size_text=25, size_title=50,
                  add_border=False, debug=False, show_img=False):
    """

    :param img:
    :param bg: back ground
    :param net: Which model to use
    :param path_font_title: folder store font for title
    :param path_font_song: folder store font for song
    :param js_txt: text data
    :param align: alignment
    :param blur: Blur or not
    :param add_border: Add border or not
    :param show_img: show picture or not
    :return:
    """

    if align not in ['left', 'center', 'right']:
        print("Align format is wrong")
        return False
    elif os.path.isfile(img) is False:
        print(f'Not found {img}')
        return None
    elif os.path.isfile(path_font_title) is False:
        print(f"{path_font_title} was not found")
        return False
    elif os.path.isfile(path_font_song) is False:
        print(f"{path_font_song} was not found")
        return False

    if img.lower().endswith(('.png', '.jpg', '.jpeg')) is False:
        print("Image format is not True")
        return False

    if blur:
        back_ground = Image.open(bg)
        back_ground_ = back_ground.filter(ImageFilter.GaussianBlur(7))
        if show_img:
            back_ground_.show()

        bg = BytesIO()
        back_ground_.save(bg, format='png')

    old, im, _pred, _pred_blur = get_object(img, net, show_img=show_img)
    if debug:
        _pred.show()
        _pred_blur.show()

    if align == 'left':
        _object_img, width_ob = change_location(old, coordinate=(W, H), size_img=(W, H),
                                                template=1, show_orig=show_img)
        _pred_img, width_ob = change_location(old, coordinate=(W, H), size_img=(W, H),
                                              template=1, show_orig=show_img)
        _pred_blur, width_ob = change_location(old, coordinate=(W, H), size_img=(W, H),
                                               template=1, show_orig=show_img)

    else:
        _object_img, width_ob = change_location(old, coordinate=(0, H), size_img=(W, H),
                                                template=1, show_orig=show_img)
        _pred_img, width_ob = change_location(_pred, coordinate=(0, H), size_img=(W, H),
                                              template=1, show_orig=show_img)
        _pred_blur, width_ob = change_location(_pred_blur, coordinate=(0, H), size_img=(W, H),
                                               template=1, show_orig=show_img)

    object_img = BytesIO()
    _object_img.save(object_img, format='png')
    if debug:
        _pred_img.show()
        _pred_blur.show()

    rgb = change(object_img, bg, net, pred=_pred_img, pred_blur=_pred_blur,
                 save_status=False, blur=True, show_orig=False)
    if debug:
        rgb.show()
    new_background = BytesIO()
    rgb.save(new_background, format='png')

    if add_border:
        rgb = add_margin(rgb, 5, 5, 5, 5, (255, 255, 255))

    if show_img:
        rgb.show()
    try:
        image = face_recognition.load_image_file(rgb)
        locations = face_recognition.face_locations(image)
    except:
        print("can not find face object in image")
        return False
    if len(locations) == 0:
        print("can not find face object in image")
        return False

    face_zone = width_face(locations)

    template = BytesIO()
    rgb.save(template, format='png')

    path = draw_list(im_ob=template, path_font_title=path_font_title,
                     black_zone=face_zone, path_output=path_output,
                     path_font_song=path_font_song, js_txt=js_txt,
                     size_title=size_title, size_text=size_text,
                     width_ob=width_ob,
                     alignment=align, show_img=show_img)

    return path


if __name__ == '__main__':
    path_background = './develop_env/images/background/background.jpg'
    path_folder = './develop_env/images/task'
    path_font_title = './develop_env/font3d/3d-noise.ttf'
    path_font_song = './develop_env/font2d/True2D.ttf'
    path_output = './develop_env'

    list_ob = os.listdir(path_folder)
    # path_ground = f"{path_folder}/{list_ob[random.randint(0,len(list_ob)-1)]}"
    path_ground = "./develop_env/object/pexels-min-an-1066116.jpg"
    print(path_ground)
    # path_ground = "../../develop_env/object/stock-photo-1019919200.jpg"
    data = {}

    try:
        with open('./develop_env/data/list_song.json') as json_file:
            data = json.load(json_file)
            print(data)
    except ValueError as error:
        print(error)

    path_model = './image_processing/lib/object_segment/u2net.pth'

    net = load_model(path_model, model_name='u2net')

    print(template_list(path_ground, path_background, net,
                        path_font_title=path_font_title,
                        path_font_song=path_font_song,
                        path_output=path_output,
                        js_txt=data, align='right',
                        size_text=25, size_title=50,
                        debug=True,
                        add_border=False, show_img=False))