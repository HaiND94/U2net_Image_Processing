"""""""""""""""""""""""
Author : NGUYEN DINH HAI
VER    : 1.0
DATE   : 2021, JAN 26
"""""""""""""""""""""""


import os
import configparser
import face_recognition

from io import  BytesIO
from datetime import datetime

from PIL import Image

try:
    from .text_insert import draw_text_multi_line
except:
    from text_insert import draw_text_multi_line


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
RATE_LM = float(details_dict["limit_rate"])
RANGE_WIDTH = int(details_dict["range_width"])


# Convert format for crop
def convert_coordinate(list_coordinate, weight):
    """
Detail: Convert coordinate from face detect coordinate follow crop function in
    :param list_coordinate: list coordinate follow (top, right, bottom, left)
    :return: new list coordinate follow (left, upper, right, lower)
    """
    # New list to save new coordinate
    face_crop = []
    dis_crop = []
    size_list = []

    # Change format follow crop function
    for coordinate in list_coordinate:
        face_crop.append([coordinate[3], coordinate[0], coordinate[1], coordinate[2]])
        dis_face_box = coordinate[1]-coordinate[3]
        h_default = int((int(weight/len(list_coordinate))-dis_face_box)/2)
        # print(h_default)
        if coordinate[3]-h_default > 0:
            dis_left = h_default
        else:
            dis_left = coordinate[3]

        if h_default < weight/len(list_coordinate):
            dis_right = h_default
        else:
            dis_right = int(weight/len(coordinate)) - coordinate[3]

        dis_crop.append(min(dis_left, dis_right))

    # Process coordinate follow weigh param
    for i in range(len(face_crop)):
        face_crop[i][0] = face_crop[i][0] - dis_crop[i]
        face_crop[i][2] = face_crop[i][2] + dis_crop[i]
        face_crop[i][1] = 0
        face_crop[i][3] = H
        size_list.append(face_crop[i][2]-face_crop[i][0])

    del dis_crop

    return face_crop, sum(size_list)


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


def _resize(list_img, show_img=False):
    """
    Detail : thi function to resize image to Height size follow config file
    :param list_img: list of image input
    :return: new list or False
    """

    if len(list_img) != 3:
        print("Input image must be 3")
        return False

    new_list = []
    for img in list_img:
        if img.lower().endswith(('.png', '.jpg', '.jpeg')) is False:
            print(f"{img} format is not True")
            return False
        if os.path.isfile(img) is False:
            print(f"Image was not found")
            return False

        im = Image.open(img)
        width, height = im.size

        if height != H:
            width = int(width*(H/height))
            im = im.resize((width, H))
        if show_img: im.show()

        new_list.append(im)

    del im, list_img

    return new_list


def _check_face_size(list_img):
    """

    """
    face_areas = []
    face_width_centers = []
    face_height_centers = []
    list_ims = _resize(list_img)
    if list_ims is False:
        return False

    for index, im in enumerate(list_ims):
        _face_im = face_recognition.load_image_file(im)
        _face_location = face_recognition.face_locations(_face_im)

        if len(_face_location) != 0:
            s, center_width, center_height = _face_attribute(_face_location)
            face_areas.append(s)
            face_width_centers.append(center_width)
            face_height_centers.append(center_height)
        else:
            print(f"Face was not found in the picture {list_img[index]}")
            return False

    # if not found face
    if False in face_areas:
        return False

    # Check size face:
    min_area = min(face_areas)
    max_area = max(face_areas)
    if max_area >= RATE_LM * min_area:
        print("The file not compatible")
        return False

    min_width = min(face_height_centers)
    max_width = max(face_height_centers)
    if (max_width - min_width) > RANGE_WIDTH:
        print("The file not compatible")
        return False

    return True


# Crop multi image and return result
def crop_multi_image(list_img, path_font_title, path_output, text='', size_txt=80, show_img=False):
    """
    Detail : This is main function to process crop multi image and paste in to the frame
    :param list_img:
    :param path_font_title:
    :param path_output:
    :param text:
    :param size_txt:
    :param show_img:
    :return:
    """

    if os.path.isdir(path_output) is False:
        print(f"{path_output} was not found")
        return False
    elif os.path.isfile(path_font_title) is False:
        print(f"{path_font_title} was not found")
        return False

    if _check_face_size(list_img) is False:
        return False

    if len(list_img) > 1:
        face_list = []
        image_list = []
        list_size = []

        # Image processing
        for file in list_img:
            if os.path.isfile(file) is False:
                print(f"{file} was not found")
                return False

            img_origin = Image.open(file)
            width, height = img_origin.size
            new_size = (int(width*(H/height)), H)

            list_size.append(int(width*(H/height)))
            img = img_origin.resize(new_size)

            if show_img: img.show()
            image = face_recognition.load_image_file(img)
            location = face_recognition.face_locations(image)
            if len(location) == 0:
                return False

            if len(image) != 0:
                face_list.append(location[0])
                image_list.append(img)
            else:
                return False

        # Coordinate processing
        weight = min(list_size)*len(face_list) if min(list_size)*len(face_list) < W else W
        crop_coordinate_list, weight = convert_coordinate(face_list, weight)

        new_image = Image.new('RGB', (weight, H), (250, 250, 250))
        with_new = 0

        # Start and paste new image to image background
        for i in range(len(crop_coordinate_list)):
            new_img = image_list[i].crop(tuple(crop_coordinate_list[i]))

            if show_img: new_img.show()

            new_image.paste(new_img, (with_new, 0))
            with_new += new_img.size[0]

        # Show image
        if show_img: new_image.show()

        template = BytesIO()
        new_image.save(template, format='png')
        path = draw_text_multi_line(im_ob=template, path_font=path_font_title, path_output=path_output, text=text,
                                    size_txt=size_txt, width_left=0.05, width_right=0.95, height_align="bottom")

        del new_img, template
        return path

    print("List_img must be a list")
    return False


if __name__ == '__main__':
    # Path to image
    path_folder = ('./develop_env/images/task/dantruong.jpg', './develop_env/images/task/quangvinh.jpg',
                   "./develop_env/images/task/unghoangphuc.jpg")
    path_font_title = "./develop_env/font3d/simson.ttf"
    path_out = './develop_env'
    text = "This is program for test case"

    # Crop
    print(crop_multi_image(path_folder, path_output=path_out,
                           path_font_title=path_font_title,
                           text=text, size_txt=50, show_img=True))