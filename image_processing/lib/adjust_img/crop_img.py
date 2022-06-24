from PIL import Image

try:
    from object_segment import predict
except:
    from ..object_segment import predict


import face_recognition
import numpy as np


def crop_img(net, im, debug):
    """
    Detail :
    :param im:
    :param debug:
    :return:
    """
    if debug:
        im.show()
    try:
        image_check = face_recognition.load_image_file(im)
        location = face_recognition.face_locations(image_check)
    except:
        return im

    if len(location) != 1:
        return im

    width, height = im.size

    dis_width = location[0][1] - location[0][3]
    dis_height = location[0][2] - location[0][0]

    # Use model for detect people
    pred, pred_blur = predict(net, np.array(im), show_img=debug)
    _pred = pred.resize(im.size, resample=Image.BILINEAR)
    ob_box = _pred.getbbox()
    _bottom_coordinate = bottom = location[0][2] + int(3 * dis_height) \
        if (location[0][2] + int(3 * dis_height)) < height else height

    del pred, _pred
    if _bottom_coordinate > ob_box[3]:
        return im

    # Calculator coordinate for crop
    top = 0
    bottom = location[0][2] + int(2.5 * dis_height) if (location[0][2] + int(2.5 * dis_height)) < height else height
    left = location[0][3] - int(2.5 * dis_width) if (location[0][3] - int(2.5 * dis_width)) > 0 else 0
    right = location[0][1] + int(2.5 * dis_width) if (location[0][1] + int(2.5 * dis_width)) < width else width

    coordinate = (left, top, right, bottom)
    if debug:
        print(coordinate)
    try:
        im_new = im.crop(coordinate)
    except Exception as error:
        print(error)
        return im

    if debug:
        im_new.show()

    return im_new