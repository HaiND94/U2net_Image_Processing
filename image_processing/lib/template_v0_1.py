import os
import configparser

import matplotlib.pyplot as plt
import torch
import numpy as np
import cv2

try:
    from .text_insert import draw_text_multi_line
except:
    from text_insert import draw_text_multi_line

from io import BytesIO
from torchvision import models
from PIL import Image, ImageFilter

try:
    from .object_segment import change_location, segment_rm, add_margin
except:
    from object_segment import change_location, segment_rm, add_margin

# Apply the transformations needed
import torchvision.transforms as T

# Load file config
config = configparser.RawConfigParser()
config.read('config.cfg')
details_dict = dict(config.items('CONFIG_IMAGE'))
# Get two param max width and max height from config file
H, W = int(details_dict['height']), int(details_dict['width'])


# Define the helper function
def decode_segmap(image, source, bgimg, nc=21):
    """

    :param image:
    :param source:
    :param bgimg:
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
    foreground = cv2.cvtColor(source, cv2.COLOR_RGB2BGR)

    # Load the background input image
    back_ground = Image.open(bgimg)

    numpy_image = np.array(back_ground)
    # background = cv2.imread(bgimg)
    background = cv2.cvtColor(numpy_image, cv2.COLOR_RGBA2BGR)

    # Change the color of foreground image to RGB
    # and resize images to match shape of R-band in RGB output map
    foreground = cv2.cvtColor(foreground, cv2.COLOR_BGR2RGB)
    background = cv2.cvtColor(background, cv2.COLOR_BGR2RGB)
    foreground = cv2.resize(foreground, (r.shape[1], r.shape[0]))
    background = cv2.resize(background, (r.shape[1], r.shape[0]))

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


# Get segment
def template_multi_ob(path_ground, bgimagepath, path_font_title, text='', blurr=True, add_border=False,
                      height_align='top', show_orig=True):
    """

    :param path_ground:
    :param bgimagepath:
    :param path_font_title:
    :param text:
    :param blurr:
    :param add_border:
    :param height_align:
    :param show_orig:
    :return:
    """

    # Check folder source

    if os.path.isdir(path_ground) is False:
        print(f'Not found {path_ground}')
        return None
    try:
        net = models.segmentation.deeplabv3_resnet101(pretrained=1).eval()
    except:
        print('Cannot open model')
        return False

    if blurr:
        back_ground = Image.open(bgimagepath)
        back_ground_ = back_ground.filter(ImageFilter.BoxBlur(5))

        if show_orig:
            back_ground_.show()

        bgimagepath = BytesIO()
        # back_ground_blurr.show()
        back_ground_.save(bgimagepath, format='png')

    new_background = None
    i = 0
    list_img = os.listdir(path_ground)
    for image in list_img:
        if image.lower().endswith(('.png', '.jpg', '.jpeg')) is False:
            break
        path = f'{path_ground}/{image}'
        im = Image.open(path)
        im = segment_rm(net, im=im, show_orig=False)
        object_img = change_location(im, coordinate=(int(i * W/(len(list_img)-1)), 720),\
                                                 size_img=(W, H), template=1, show_orig=False)
        # img_new = add_margin(im, 0, i*2000, 0, abs(i-1)*2000, (0, 0, 0))
        # temp = BytesIO()
        # img_new.save(temp, format="png")
        numpy_image = np.array(object_img)
        # img = Image.open(temp)
        dev = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        # Comment the Resize and CenterCrop for better inference results
        trf = T.Compose([T.Resize(H),
                         # T.CenterCrop(224),
                         T.ToTensor(),
                         T.Normalize(mean=[0.485, 0.456, 0.406],
                                     std=[0.229, 0.224, 0.225])])
        inp = trf(object_img).unsqueeze(0).to(dev)
        out = net.to(dev)(inp)['out']
        om = torch.argmax(out.squeeze(), dim=0).detach().cpu().numpy()
        if i != 0:
            rgb = decode_segmap(om, numpy_image, new_background)
            # new_background = f'./images/background/new_background_{i}.png'
            new_background = BytesIO()
            plt.imsave(new_background, rgb, format='png')
            # Save new result
        else:
            rgb = decode_segmap(om, numpy_image, bgimagepath)
            new_background = BytesIO()
            plt.imsave(new_background, rgb, format='png')
        i += 1
    img_real = 255 * rgb
    img_pil = Image.fromarray(img_real.astype('uint8'), 'RGB')
    if add_border:
        img_pil = add_margin(img_pil, 5, 5, 5, 5, (255, 255, 255))
    # img_pil = insert_text(img_pil, path_font='./font3d', text="Ưng Hoàng Phúc - Đan Trường - Quang Vinh")
    if show_orig:
        img_pil.show()
    template = BytesIO()
    img_pil.save(template, format='png')
    # draw_text_one_line(im_ob=template, path_font='./develop_env/font3d', text=text, size_txt=20, center_alignment=True,
    #                    height_align=height_align)
    draw_text_multi_line(im_ob=template, path_font=path_font_title, text=text, size_txt=30, width_left=0.2,
                         width_right=0.8, height_align="top")
    # insert_text(im_ob=template, path_font='./font3d')


if __name__ == '__main__':
    path_background = './develop_env/images/background/trang.jpg'
    path_ground = './develop_env/images/task'
    list_ground = os.listdir(path_ground)
    path_font_title = './develop_env/font3d'
    text = 'Ung Hoang Phuc - Dan Truong - Quang Vinh'
    template_multi_ob(path_ground, path_background, path_font_title, blurr=True, text=text, add_border=True, show_orig=False)