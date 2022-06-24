"""""""""""
Author : Nguyen Dinh Hai
Date   : 18 Jan 2021
version: 0.0
"""""""""""

import matplotlib.pyplot as plt
import torch
import numpy as np
import cv2

from io import BytesIO

from matplotlib import cm

from torchvision import models
from PIL import Image
# Apply the transformations needed
import torchvision.transforms as T


# Add padding for image which we need to change
def add_margin(pil_img, top, right, bottom, left, color):
    width, height = pil_img.size
    new_width = width + right + left
    new_height = height + top + bottom
    result = Image.new(pil_img.mode, (new_width, new_height), color)
    result.paste(pil_img, (left, top))
    return result


# Define the helper function
def decode_segmap(image, source, nc=21):
    """

    :param image:
    :param source:
    :param nc:
    :return:
    """
    label_colors = np.array([(0, 0, 0),  # 0=background
                             # 1=aeroplane, 2=bicycle, 3=bird, 4=boat, 5=bottle
                             (128, 0, 0), (0, 128, 0), (128, 128, 0), (0, 0, 128), (128, 0, 128),
                             # 6=bus, 7=car, 8=cat, 9=chair, 10=cow
                             (0, 128, 128), (128, 128, 128), (64, 0, 0), (192, 0, 0), (64, 128, 0),
                             # 11=dining table, 12=dog, 13=horse, 14=motorbike, 15=person
                             (192, 128, 0), (64, 0, 128), (192, 0, 128), (64, 128, 128), (192, 128, 128),
                             # 16=potted plant, 17=sheep, 18=sofa, 19=train, 20=tv/monitor
                             (0, 64, 0), (128, 64, 0), (0, 192, 0), (128, 192, 0), (0, 64, 128)])

    r = np.zeros_like(image).astype(np.uint8)
    g = np.zeros_like(image).astype(np.uint8)
    b = np.zeros_like(image).astype(np.uint8)

    for l in range(0, nc):
        idx = image == l
        r[idx] = label_colors[l, 0]
        g[idx] = label_colors[l, 1]
        b[idx] = label_colors[l, 2]

    rgb = np.stack([r, g, b], axis=2)

    # Load the foreground input image
    # foreground = cv2.imread(source)
    numpy_image = np.array(source)
    foreground = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)

    # Change the color of foreground image to RGB
    # and resize image to match shape of R-band in RGB output map
    foreground = cv2.cvtColor(foreground, cv2.COLOR_BGR2RGB)
    foreground = cv2.resize(foreground, (r.shape[1], r.shape[0]))

    # Create a background array to hold white pixels
    # with the same size as RGB output map
    background = 0 * np.ones_like(rgb).astype(np.uint8)

    # Convert uint8 to float
    foreground = foreground.astype(float)
    background = background.astype(float)

    # Create a binary mask of the RGB output map using the threshold value 0
    th, alpha = cv2.threshold(np.array(rgb), 0, 255, cv2.THRESH_BINARY)

    # Apply a slight blur to the mask to soften edges
    alpha = cv2.GaussianBlur(alpha, (7, 7), 0)

    # Normalize the alpha mask to keep intensity between 0 and 1
    alpha = alpha.astype(float) / 255

    # Multiply the foreground with the alpha matte
    foreground = cv2.multiply(alpha, foreground)

    # Multiply the background with ( 1 - alpha )
    background = cv2.multiply(1.0 - alpha, background)

    # Add the masked foreground and background
    outImage = cv2.add(foreground, background)

    # Return a normalized output image for display
    return outImage / 255


# Get segment image
def segment(net, im, coordinate, size_img, show_orig=True):
    """
    :param net:
    :param path:
    :param coordinate:
    :param size_img:
    :param show_orig:
    :return:
    """
    # Open image follow path input
    # im = Image.open(path)
    coordinate = list(coordinate)
    dev = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    if show_orig: plt.imshow(im); plt.axis('off'); plt.show()
    # Comment the Resize and CenterCrop for better inference results
    trf = T.Compose([T.Resize(450),
                     # T.CenterCrop(224),
                     T.ToTensor(),
                     T.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])])
    inp = trf(im).unsqueeze(0).to(dev)
    out = net.to(dev)(inp)['out']
    om = torch.argmax(out.squeeze(), dim=0).detach().cpu().numpy()

    rgb = decode_segmap(om, im)

    # Find edge for object
    # max_x = right --- max_y = bottom
    max_x = max_y = 0
    # minx = left
    min_x = rgb.shape[0]
    # min_y = top
    min_y = rgb.shape[1]
    # Get value i, j to crop object
    for i in range(rgb.shape[0]):
        for j in range(rgb.shape[1]):
            if max(rgb[i][j]) != 0:
                min_x = i if i < min_x else min_x
                min_y = j if j < min_y else min_y
                max_x = i if i > max_x else max_x
                max_y = j if j > max_y else max_y

    # New image which was cropped
    crop_img = 255*rgb[min_x:max_x, min_y:max_y, :]
    new_img = Image.fromarray(crop_img.astype('uint8'), 'RGB')

    # Get contribute of crop_img
    if show_orig: new_img.show()
    width_ob, height_ob = new_img.size

    # Check size of image background with size object
    if width_ob > size_img[0] or height_ob > size_img[1]:
        div = max(width_ob/size_img[0], height_ob/size_img[1])
        width_ob = int(width_ob/div)
        height_ob = int(height_ob/div)

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
    # print(coordinate)

    # Calculate parm for add_margin function
    top = coordinate[1] - center_ob[1]
    left = coordinate[0] - center_ob[0]
    bottom = size_img[1] - (top + height_ob)
    right = size_img[0] - (left + width_ob)
    color = (0, 0, 0)   # Define with black ground

    # print(f'Top is:{top} \n Right is:{right} \n Bottom is: {bottom} \n Left is: {left}')

    # Canvas_img to fit with background
    canvas_img = add_margin(new_img, top=top, right=right, bottom=bottom, left=left, color=color)

    if show_orig:
        canvas_img.show()
        #canvas_img.save('../../images/ouput/canvas_img.png')

    return canvas_img


# Run function in module
if __name__ == '__main__':
    dlab = models.segmentation.deeplabv3_resnet101(pretrained=1).eval()
    path = '../../../develop_env/images/ground/girl.png'
    img = Image.open(path)
    segment(dlab, im=img, coordinate=(100, 100), size_img=(1280, 720), show_orig=True)
