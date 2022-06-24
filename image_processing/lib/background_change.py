"""""""""""""""""""""""
Author : NGUYEN DINH HAI
VER    : 1.0
DATE   : 2021, JAN 26
"""""""""""""""""""""""

import numpy as np
import os
import json
import random

import face_recognition

from io import BytesIO

from datetime import datetime

from PIL import Image, ImageFilter

try:
    from .object_segment import load_model, get_object, predict, add_margin
except:
    from object_segment import load_model, get_object, predict, add_margin

try:
    from .text_insert import draw_list
except:
    from text_insert import draw_list

W = 1280
H = 720


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
    # new_im = im_ob.crop((abs(W - width_new), abs(H - height_new), width_new, height_new))
    new_im = im_ob.crop((0, 0, W, H))

    del div, width_new, height_new, im_ob

    return new_im


# Chang object to new background
def _change(img, bg, net, pred=False, pred_blur=False,
            save_status=False, blur=True,
            debug=False, show_orig=False, mask=False):
    """

    :param img:
    :param bg:
    :param net:
    :param pred:
    :param pred_blur:
    :param save_status:
    :param blur:
    :param debug:
    :param show_orig:
    :return:
    """

    background = Image.open(bg)
    im = Image.open(img)

    background = background.resize(im.size)

    if show_orig:
        background.show()
        im.show()

    if pred_blur is False:
        pred, pred_blur = predict(net, np.array(im))
        _blur_mask = pred_blur.resize(im.size, resample=Image.BILINEAR)
    else:
        _blur_mask = pred_blur

    if blur:
        background = background.filter(ImageFilter.GaussianBlur(7))
    if mask is False:

        _new_blur = Image.composite(im, background, _blur_mask.convert("L"))
    else:
        _new_blur = Image.composite(im, background, mask.convert("L"))

    # _new = Image.composite(im, background, pred.convert("L"))
    # _new_blur = Image.composite(im, _new, _blur_mask.convert("L"))

    if debug:
        _blur_mask.show()
        _new_blur.show()

    if save_status:
        time = datetime.now()
        current_time = time.strftime("%H:%M:%S")
        current_date = time.date()
        path_output_folder = './output/change'
        if os.path.isdir(path_output_folder) is False:
            if os.path.isdir('./output') is False:
                os.mkdir('./output')
            os.mkdir(path_output_folder)
        path_new = f"{path_output_folder}/{current_date}_{current_time}.png"
        _new_blur.save(path_new)

        del im, pred, background, pred_blur

        return path_new

    return _new_blur


# To crawl data from youtube and change object
def swap_object(img, bg, net, path_font_title, path_output, path_font_song, js_txt,
                size_title=50, size_text=25, align="left", blur=True, show_img=False):
    """
    Detail :
    :param img:
    :param bg:
    :param net:
    :param path_font_title:
    :param path_output:
    :param path_font_song:
    :param js_txt:
    :param size_title:
    :param size_text:
    :param align:
    :param blur:
    :param show_img:
    :return:
    """

    background = Image.open(bg)
    im = Image.open(img)

    if show_img:
        print(im.size)
        im.show()

    width, height = im.size

    # if height > 0.7 * width:
    #     return False

    im = _resize(im, width, height)

    image = face_recognition.load_image_file(im)
    locations = face_recognition.face_locations(image)
    if len(locations) != 0:
        print(locations)
        face_left = locations[0][3]
        face_right = locations[0][1]
        if (face_left > W/5) and (face_right > 4*W/5):
            align = "center"

        elif face_left < W/5:
            align = "right"

        elif face_right > 4*W/5:
            align = "left"

    if show_img:
        print(im.size)

    background = background.resize(im.size)

    if show_img:
        background.show()
        im.show()

    pred, pred_blur = predict(net, np.array(im))

    _blur_mask = pred_blur.resize(im.size, resample=Image.BILINEAR)
    if blur:
        background = background.filter(ImageFilter.GaussianBlur(7))
    _new_blur = Image.composite(im, background, _blur_mask.convert("L"))
    if show_img:
        _new_blur.show()

    template = BytesIO()
    _new_blur.save(template, format='png')

    path = draw_list(im_ob=template, path_font_title=path_font_title,
                     black_zone=[], path_output=path_output,
                     path_font_song=path_font_song, js_txt=js_txt,
                     size_title=size_title, size_text=size_text,
                     template="change",
                     alignment=align, show_img=show_img)

    return path


# To use for other module
def change(img, bg, net, pred=False, pred_blur=False,
           save_status=False, blur=True, show_orig=False, mask=False):

    new_img = _change(img, bg, net, pred=pred, pred_blur=pred_blur,
                      save_status=save_status, blur=blur, show_orig=show_orig, mask=mask)
    return new_img


if __name__ == '__main__':
    path_background = './develop_env/images/background/background.jpg'
    path_folder = './develop_env/images/task'
    path_font_title = './develop_env/font3d/3d-noise.ttf'
    path_font_song = './develop_env/font2d/True2D.ttf'
    path_output = './develop_env'

    # list_ob = os.listdir(path_folder)
    # path_ground = f"{path_folder}/{list_ob[random.randint(0, len(list_ob) - 1)]}"
    # print(path_ground)
    # path_ground = "./develop_env/images/error.jpg"
    path_ground = "./develop_env/object/pexels-ali-pazani-2887718.jpg"
    data = {}

    try:
        with open('./develop_env/data/list_song.json') as json_file:
            data = json.load(json_file)
            print(data)
    except ValueError as error:
        print(error)

    path_model = './image_processing/lib/object_segment/u2net.pth'

    net = load_model(path_model, model_name='u2net')

    print(swap_object(path_ground, path_background, net,
                      path_font_title=path_font_title,
                      path_font_song=path_font_song,
                      path_output=path_output,
                      js_txt=data, align='left',
                      size_text=30, size_title=50,
                      show_img=True))