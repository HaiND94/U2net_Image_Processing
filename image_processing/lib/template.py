import os
import configparser
import face_recognition

import matplotlib.pyplot as plt
import numpy as np


try:
    from .text_insert import draw_text_multi_line
except:
    from text_insert import draw_text_multi_line

try:
    from .object_segment import load_model, get_object, predict, add_margin, change_location
except:
    from object_segment import load_model, get_object, predict, add_margin, change_location

try:
    from background_change import change
except:
    from .background_change import change

from datetime import datetime
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


# Calculator area of face region
def _face_attribute(face_location):
    if len(face_location) == 0 or False:
        print("Face not found")
        return False
    try:
        face_center = int((face_location[0][1]+face_location[0][3])/2)
        s = (face_location[0][2] - face_location[0][0]) * (face_location[0][3] - face_location[0][1])
    except Exception as error:
        print(error)
        return False

    return abs(s), face_center


# Arrange image
def arrange_img(ob_img, sum_ob, face_center, i=0, show_orig=False):

    # Get contribute of crop_img
    width_ob, height_ob = ob_img.size
    # Check size of image background with size object
    if width_ob > W or height_ob > H:
        ob_img = ob_img.resize((W, H), Image.ANTIALIAS)
        width_ob, height_ob = ob_img.size
        _face_im = face_recognition.load_image_file(ob_img)
        _face_location = face_recognition.face_locations(_face_im)
        try:
            s, face_center = _face_attribute(_face_location)
        except Exception as error:
            print(error)
            return False
    if i == 0:
        if face_center > int(W/(2*sum_ob)):
            print(face_center)
            ob_img = ob_img.crop(((face_center-W/(2*sum_ob)), 0, width_ob, height_ob))
            face_center = W/(2*sum_ob)
            width_ob, height_ob = ob_img.size
    elif i == sum_ob:
        if (width_ob - face_center) > int(W/(2*sum_ob)):
            ob_img = ob_img.crop((0, 0, face_center + W/(2*sum_ob), height_ob))
            width_ob, height_ob = ob_img.size

    top = int(H - height_ob)
    left = int((2*i+1) * (W/(2*sum_ob)) - face_center)
    bottom = 0
    right = int(W - (2*i+1) * (W/(2*sum_ob)) + face_center - width_ob)
    color = (0, 0, 0)  # Define with black ground

    # print(f'Top is:{top} \n Right is:{right} \n Bottom is: {bottom} \n Left is: {left}')

    # Canvas_img to fit with background
    canvas_img = add_margin(ob_img, top=top, right=right, bottom=bottom, left=left, color=color)
    if show_orig:
        canvas_img.show()
        # canvas_img.save('../../images/ouput/canvas_img.png')

    return canvas_img


# Start processing
def template_multi_ob(list_img, bg, path_font_title, net, text='', blur=True, add_border=False, show_orig=False):
    """

    :param list_img:
    :param bg:
    :param path_font_title:
    :param net:
    :param text:
    :param blur:
    :param add_border:
    :param height_align:
    :param show_orig:
    :return:
    """

    if len(list_img) == 0:
        print('Images input must be a list')
        return False
    else:
        for file in list_img:
            if os.path.isfile(file) is False:
                print(f"File {file} not found")
                return False
    if os.path.isfile(bg) is False:
        print('Not found file background')
        return False

    if os.path.isfile(path_font_title) is False:
        print("Not found font")
        return False

    if blur:
        back_ground = Image.open(bg)
        back_ground_ = back_ground.filter(ImageFilter.BoxBlur(5))

        if show_orig:
            back_ground_.show()

        bg = BytesIO()
        back_ground_.save(bg, format='png')

    new_background = None
    face_areas = []
    face_centers = []
    object_imgs = []

    # Check validate input
    for image in list_img:
        if image.lower().endswith(('.png', '.jpg', '.jpeg')) is False:
            return False
        im = get_object(image, net, show_img=show_orig)
        if im is False:
            return False
        object_imgs.append(im)

    for img in object_imgs:
        # _im = Image.open(img)
        _face_im = face_recognition.load_image_file(img)
        _face_location = face_recognition.face_locations(_face_im)
        if len(_face_location) != 0:
            s, center = _face_attribute(_face_location)
            face_areas.append(s)
            face_centers.append(center)
        else:
            print("Face was not found in the picture")
            return False

    # if not found face
    if False in face_areas:
        return False

    min_area = min(face_areas)

    # Check condition face areas not beautiful in one picture
    for face_area in face_areas:
        if face_area >= 3*min_area:
            print("The file not compatible")
            return False

    for i in range(len(object_imgs)):
        _object_img = arrange_img(ob_img=object_imgs[i], face_center=face_centers[i], sum_ob=len(object_imgs), i=i)
        object_img = BytesIO()
        _object_img.save(object_img, format='png')

        if i != 0:
            rgb = change(object_img, new_background, net, save_status=False, blur=False, show_orig=show_orig)
            # new_background = f'./images/background/new_background_{i}.png'
            new_background = BytesIO()
            rgb.save(new_background, format='png')
            # Save new result
        else:
            rgb = change(object_img, bg, net, save_status=False, blur=True, show_orig=show_orig)
            new_background = BytesIO()
            rgb.save(new_background, format='png')
        i += 1

    if add_border:
        rgb = add_margin(rgb, 5, 5, 5, 5, (255, 255, 255))

    if show_orig:
        rgb.show()

    if text == '':
        time = datetime.now()
        current_time = time.strftime("%H:%M:%S")
        current_date = time.date()
        path_output_folder = './output/template'

        if os.path.isdir(path_output_folder) is False:
            if os.path.isdir('./output') is False:
                os.mkdir('./output')
            os.mkdir(path_output_folder)

        path_new = f"{path_output_folder}/{current_date}_{current_time}.png"
        rgb.save(path_new)
        return 0

    template = BytesIO()
    rgb.save(template, format='png')
    draw_text_multi_line(im_ob=template, path_font=path_font_title, text=text, size_txt=45, width_left=0.2,
                         width_right=0.8, height_align="top", show_img=show_orig)


if __name__ == '__main__':
    list_img = ['./develop_env/images/task/dantruong.jpg', './develop_env/images/task/quangvinh.jpg',
                './develop_env/images/task/unghoangphuc.jpg']
    bg = "./develop_env/images/background/background.jpg"
    path_model = './image_processing/lib/object_segment/u2net.pth'
    path_font = "./develop_env/font3d/3d-noise.ttf"
    text = "TOP 2020"

    # print(img.size)

    net = load_model(path_model, model_name='u2net')
    template_multi_ob(list_img, bg, path_font, net, text=text, blur=True, add_border=False, show_orig=True)
