import face_recognition
import io
import os
import configparser
import random

from io import BytesIO

from PIL import Image, ImageFilter, ImageDraw


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
W_OFFSET = int(details_dict["weight_offset"])
WIDTH_LINE = int(details_dict["with_line"])
RATE_LM = float(details_dict["limit_rate"])


# Convert format for crop
def _convert_coordinate(list_coordinate, weight):
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

        dis_left = h_default if coordinate[3]-h_default > 0 else coordinate[3]
        dis_right = h_default if h_default < weight/len(list_coordinate) else \
            int(weight/len(coordinate)) - coordinate[3]
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


def _check_img(img):
    if os.path.isfile(img) is False:
        print(f"{img} was not found")
        return False
    if img.lower().endswith(('.png', '.jpg', '.jpeg')) is False:
        print(f"{img} format is not True")
        return False

    return True


# Calculator area of face region
def _face_attribute(face_location):
    if len(face_location) == 0 or False:
        print("Face not found")
        return False
    try:
        # face_center = int((face_location[0][1]+face_location[0][3])/2)
        s = (face_location[0][2] - face_location[0][0]) * (face_location[0][3] - face_location[0][1])
    except Exception as error:
        print(error)
        return False

    return abs(s)


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
    for idx, coordinate in enumerate(list_coordinate):
        face_crop.append([coordinate[3], coordinate[0], coordinate[1], coordinate[2]])
        dis_face_box = coordinate[1]-coordinate[3]
        h_default = int((int(weight/len(list_coordinate))-dis_face_box)/2)

        dis_left = h_default if coordinate[3]-h_default > 0 else coordinate[3]
        dis_right = h_default if h_default < weight/len(list_coordinate) else \
            int(weight/len(coordinate)) - coordinate[3]
        dis_crop.append(min(dis_left, dis_right))

    # Process coordinate follow weigh param
    for i in range(len(face_crop)):
        face_crop[i][0] = face_crop[i][0] - dis_crop[i] - int(W_OFFSET/2)
        face_crop[i][2] = face_crop[i][2] + dis_crop[i] + int(W_OFFSET/2)
        face_crop[i][1] = 0
        face_crop[i][3] = H
        size_list.append(face_crop[i][2]-face_crop[i][0])

    del size_list

    return face_crop


def _resize(list_images):
    """
    Detail : thi function to resize image to Height size follow config file
    :param list_images: list of image input
    :return: new list or False
    """

    if len(list_images) != 3:
        print("Input image must be 3")
        return False

    new_list = []
    for img in list_images:
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

        new_list.append(im)

    del im, list_images

    return new_list


def _check_face_size(list_ims, list_images):
    """
    Detail: this function to check face condition
    :param list_images: list of image input
    :return: face center coordinate
    """

    face_areas = []
    face_coordinate = []

    if list_ims is False:
        return False

    for index, im in enumerate(list_ims):
        _face_im = face_recognition.load_image_file(im)
        _face_location = face_recognition.face_locations(_face_im)

        if len(_face_location) != 0:
            s = _face_attribute(_face_location)
            face_areas.append(s)
            face_coordinate.append(_face_location[0])
        else:
            print(f"Face was not found in the picture {list_images[index]}")
            return False

    # if not found face
    if False in face_areas:
        return False

    # Check size face:
    min_area = min(face_areas)
    max_area = max(face_areas)
    if max_area >= RATE_LM*min_area:
        print("The file not compatible")
        return False

    return face_coordinate


def process_img(list_im, face_list, show_img=False):
    """
    Detail : Crop and paste image from image follow template
    :param show_img: to show picture for debug
    :param face_list:
    :param list_im: list image was open by PIL
    :param : list face center coordinate
    :return:
    """

    crop_coordinate_list = convert_coordinate(face_list, W)
    mode = random.randint(1, 2)

    if len(crop_coordinate_list) != 3:
        print("Can not found enough coordinate!")
        return False

    new_img_1 = None
    new_img_2 = None
    new_img_3 = None
    _distance = int(W/3)

    for idx, im in enumerate(list_im):
        new_img = im.crop(tuple(crop_coordinate_list[idx]))

        if show_img: new_img.show()

        if idx == 0:
            img = Image.new('RGB', (W, H), (0, 0, 0))
            draw = ImageDraw.Draw(img)

            if mode == 1:
                draw.polygon(((_distance + W_OFFSET-WIDTH_LINE, 0), (W, 0), (W, H),
                              (_distance - W_OFFSET, H)), fill=(255, 255, 255))
            else:
                draw.polygon(((_distance - W_OFFSET, 0), (W, 0), (W, H),
                              (_distance + W_OFFSET - WIDTH_LINE, H)), fill=(255, 255, 255))

            img = img.filter(ImageFilter.GaussianBlur(4))

            # add padding for image number 1
            result = Image.new(new_img.mode, (W, H), (255, 255, 255))
            result.paste(new_img, (0, 0))
            new_img_1 = Image.composite(img, result, img.convert("L"))

            if show_img:
                img.show();
                result.show()
                new_img_1.show()

        elif idx == 1:
            if new_img_1 is None:
                return False

            img = Image.new('RGB', (W, H), (255, 255, 255))
            draw = ImageDraw.Draw(img)
            if mode == 1:
                draw.polygon(((_distance + W_OFFSET, 0), (_distance * 2 - W_OFFSET, 0),
                              (W - _distance + W_OFFSET - WIDTH_LINE, H), (_distance - W_OFFSET + WIDTH_LINE, H)),
                             fill=(0, 0, 0))
            else:
                draw.polygon(((_distance - W_OFFSET + WIDTH_LINE, 0), (_distance * 2 + W_OFFSET - WIDTH_LINE, 0),
                              (W - _distance - W_OFFSET, H), (_distance + W_OFFSET, H)),
                             fill=(0, 0, 0))

            img = img.filter(ImageFilter.GaussianBlur(4))

            # add padding for image number 2
            width, height = new_img.size
            result = Image.new(new_img.mode, (W, H), (255, 255, 255))
            result.paste(new_img, (width - W_OFFSET - WIDTH_LINE, 0))
            new_img_2 = Image.composite(new_img_1, result, img.convert("L"))

            if show_img:
                result.show()
                im.show()
                new_img_2.show()

        elif idx == 2:
            if new_img_2 is None:
                return False

            img = Image.new('RGB', (W, H), (255, 255, 255))
            draw = ImageDraw.Draw(img)
            if mode == 1:
                draw.polygon(((W - _distance - W_OFFSET + WIDTH_LINE, 0), (W, 0),
                              (W, H), (W - _distance + W_OFFSET, H)),
                             fill=(0, 0, 0))
            else:
                draw.polygon(((W - _distance + W_OFFSET, 0), (W, 0),
                              (W, H), (W - _distance - W_OFFSET + WIDTH_LINE, H)),
                             fill=(0, 0, 0))
            img = img.filter(ImageFilter.GaussianBlur(4))

            # add padding for image number 2
            width, height = new_img.size
            result = Image.new(new_img.mode, (W, H), (255, 255, 255))
            result.paste(new_img, (W - width, 0))
            new_img_3 = Image.composite(new_img_2, result, img.convert("L"))

            if show_img:
                result.show()
                im.show()
                new_img_3.show()

    if new_img_3 is None:
        return False

    template = BytesIO()
    new_img_3.save(template, format="png")

    del new_img, new_img_1, new_img_2, draw

    return template


def template_crop(list_images, path_font_title, path_output, text='', size_txt=80, show_img=False):
    """
Detail : This function is main function to process image from a list image
    :param list_images:
    :param path_font_title:
    :param path_output:
    :param text:
    :param size_txt:
    :param show_img:
    :return:
    """

    if os.path.isfile(path_font_title) is False:
        print(f"{path_font_title} was not found")
        return False
    if path_font_title.lower().endswith(('.ttf', '.tof')) is False:
        print(f"{path_font_title} format is not True")
        return False
    if os.path.isdir(path_output) is False:
        print(f"{path_output} was not found")
        return False

    number_of_img = len(list_images)
    if number_of_img != 3:
        print(f"{list_images} format not true")
        return False

    new_ims = _resize(list_images)
    list_faces_coordinate = _check_face_size(new_ims, list_images)
    if list_faces_coordinate is False:
        return False

    new_img = process_img(list_im=new_ims, face_list=list_faces_coordinate, show_img=show_img)

    path = draw_text_multi_line(im_ob=new_img, path_font=path_font_title, path_output=path_output, text=text,
                                size_txt=size_txt, width_left=0.05, width_right=0.95, height_align="bottom",
                                show_img=show_img)

    del new_img

    return path


if __name__ == "__main__":

    list_img = ['./develop_env/images/task/dantruong.jpg', './develop_env/images/task/quangvinh.jpg',
                "./develop_env/images/task/unghoangphuc.jpg"]
    path_font_title = "./develop_env/font3d/simson.ttf"
    path_out = './develop_env'
    text = "This is program for test case"

    print(template_crop(list_images=list_img, text=text, path_output=path_out, path_font_title=path_font_title,
                        size_txt=50,
                        show_img=True))

