"""""""""""""""""""""""
Author : NGUYEN DINH HAI
VER    : 1.0
DATE   : 2021, JAN 26
"""""""""""""""""""""""
import os
import errno
import time
import io

import numpy as np
from numpy import asarray

from PIL import Image
# from skimage import transform

import torch
import torch.nn as nn
import torch.nn.functional as F
# from torch.autograd import Variable

import torchvision
from torchvision import transforms  # , utils

try:
    from .u2net import utils, model
except:
    from u2net import utils, model


# Add padding for image which we need to change
def add_margin(pil_img, top, right, bottom, left, color):
    """

    :param pil_img:
    :param top:
    :param right:
    :param bottom:
    :param left:
    :param color:
    :return:
    """
    width, height = pil_img.size
    new_width = width + right + left
    new_height = height + top + bottom
    result = Image.new(pil_img.mode, (new_width, new_height), color)
    result.paste(pil_img, (left, top))
    return result


def load_model(path, model_name: str = 'u2net'):

    if model_name == "u2netp":
        net = model.U2NETP(3, 1)
    elif model_name == "u2net":
        net = model.U2NET(3, 1)
    else:
        print("Choose between u2net or u2netp")
    print(f"INFO:root: Loaded {model_name}")

    try:
        with open(path, 'rb') as f:
            buffer = io.BytesIO(f.read())
    except FileNotFoundError:
        raise FileNotFoundError(
            errno.ENOENT, os.strerror(errno.ENOENT)
            )

    try:
        if torch.cuda.is_available():
            net.load_state_dict(torch.load(buffer))
            net.to(torch.device("cuda"))
        else:
            net.load_state_dict(torch.load(buffer, map_location="cpu"))
    except FileNotFoundError:
        raise FileNotFoundError(
            errno.ENOENT, os.strerror(errno.ENOENT)
        )

    net.eval()

    return net


def norm_pred(d):
    ma = torch.max(d)
    mi = torch.min(d)
    dn = (d - mi) / (ma - mi)

    return dn


def preprocess(image):
    label_3 = np.zeros(image.shape)
    label = np.zeros(label_3.shape[0:2])

    if 3 == len(label_3.shape):
        label = label_3[:, :, 0]
    elif 2 == len(label_3.shape):
        label = label_3

    if 3 == len(image.shape) and 2 == len(label.shape):
        label = label[:, :, np.newaxis]
    elif 2 == len(image.shape) and 2 == len(label.shape):
        image = image[:, :, np.newaxis]
        label = label[:, :, np.newaxis]

    transform = transforms.Compose([utils.RescaleT(320), utils.ToTensorLab(flag=0)])
    sample = transform({"imidx": np.array([0]), "image": image, "label": label})

    return sample


def predict(net, item):

    sample = preprocess(item)

    with torch.no_grad():

        if torch.cuda.is_available():
            inputs_test = torch.cuda.FloatTensor(sample["image"].unsqueeze(0).float())
        else:
            inputs_test = torch.FloatTensor(sample["image"].unsqueeze(0).float())

        d1, d2, d3, d4, d5, d6, d7 = net(inputs_test)

        pred = d1[:, 0, :, :]
        predict = norm_pred(pred)

        predict = predict.squeeze()
        predict_np = predict.cpu().detach().numpy()
        img = Image.fromarray(predict_np * 255).convert("RGB")
        # print(img.size)
        del d1, d2, d3, d4, d5, d6, d7, pred, predict, predict_np, inputs_test, sample

        return img


# Get object from image
def get_object(img, net, show_img=False):
    im = Image.open(img)

    pred = predict(net, np.array(im))
    pred = pred.resize(im.size, resample=Image.BILINEAR)# remove resample

    if show_img: pred.show()

    empty_img = Image.new("RGB", im.size, 0)

    new = Image.composite(im, empty_img, pred.convert("L"))
    new_img = new.crop(new.getbbox())

    if show_img: new_img.show()

    del im, pred, empty_img, new

    return new_img


def change_location(im, coordinate, size_img, template=0, show_orig=False):
    """

    :param im:
    :param coordinate:
    :param size_img:
    :param template:
    :param show_orig:
    :return:
    """
    coordinate = list(coordinate)
    # Get contribute of crop_img
    width_ob, height_ob = im.size

    # Check size of image background with size object
    if width_ob > size_img[0] or height_ob > size_img[1]:
        div = max(width_ob/size_img[0], height_ob/size_img[1])
        width_ob = int(width_ob/div)
        height_ob = int(height_ob/div)
    elif template == 1:
        div = (size_img[1] - 80)/height_ob
        width_ob = int(width_ob * div)
        height_ob = (size_img[1] - 80)

    im = im.resize((width_ob, height_ob))

    # Fix coordinate to fix with object
    center_ob = (int(width_ob/2), int(height_ob/2))
    coordinate[0] = center_ob[0] if coordinate[0] < center_ob[0] \
        else coordinate[0]
    coordinate[0] = (size_img[0] - center_ob[0]) if coordinate[0] > (size_img[0]-center_ob[0]) \
        else coordinate[0]
    coordinate[1] = center_ob[1] if coordinate[1] < center_ob[1] \
        else coordinate[1]
    coordinate[1] = (size_img[1] - center_ob[1]) if coordinate[1] > (size_img[1]-center_ob[1]) \
        else coordinate[1]
    # print(f"coordinate is {coordinate}")

    # Calculate parm for add_margin function
    top = coordinate[1] - center_ob[1]
    left = coordinate[0] - center_ob[0]
    bottom = size_img[1] - (top + height_ob)
    right = size_img[0] - (left + width_ob)
    color = (0, 0, 0)   # Define with black ground

    # print(f'Top is:{top} \n Right is:{right} \n Bottom is: {bottom} \n Left is: {left}')

    # Canvas_img to fit with background
    canvas_img = add_margin(im, top=top, right=right, bottom=bottom, left=left, color=color)

    if show_orig:
        canvas_img.show()
        # canvas_img.save('../../images/ouput/canvas_img.png')

    return canvas_img


if __name__ == "__main__":
    img = '../../../develop_env/images/ground/girl.png'
    # print(img.size)
    path = '../../../model/u2net.pth'
    net = load_model(path, 'u2net')
    get_object(img=img, net=net, show_img=True)