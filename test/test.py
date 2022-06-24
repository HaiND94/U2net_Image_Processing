import os
import random
import json

from PIL import Image

try:
    from image_processing import load_model, image_processing
except:
    from ..image_processing import load_model, image_processing


def create_split_data(path_ob, path_bg):
    if os.path.isdir(path_ob) is False:
        print(f"Not found folder object {path_ob}")
        return False
    if os.path.isdir(path_bg) is False:
        print(f"Not found folder background {path_bg}")
        return False

    data = dict()
    list_index = []
    count = 0
    num_img = random.randint(2, 4)
    list_ob = os.listdir(path_ob)
    list_bg = os.listdir(path_bg)
    list_img = []

    # Get background
    background = f"{path_bg}/{list_bg[random.randint(0,len(list_bg))-1]}"
    while count < num_img:

        index = random.randint(0, len(list_ob)-1)
        if index not in list_index:
            list_img.append(f'{path_ob}/{list_ob[index]}')
            count += 1
            list_index.append(index)

    data["style"] = "split"
    data["list_img"] = list_img
    data["path_bg"] = background
    data["path_ft"] = "./develop_env/font3d/3Dumb.ttf"
    data["text"] = "This is program for test case"

    return data


def create_list_data(path_ob=None, path_bg=None):
    if os.path.isdir(path_ob) is False:
        print(f"Not found folder object {path_ob}")
        return False
    if os.path.isdir(path_bg) is False:
        print(f"Not found folder background {path_bg}")
        return False

    try:
        with open('./develop_env/data/list_song.json') as json_file:
            data_text = json.load(json_file)
    except ValueError as error:
        print(error)

    data = dict()
    list_ob = os.listdir(path_ob)
    list_bg = os.listdir(path_bg)

    # Get background
    background = f"{path_bg}/{list_bg[random.randint(0, len(list_bg)) - 1]}"
    image = f"{path_ob}/{list_ob[random.randint(0,len(list_ob)-1)]}"
    print(image)

    data["style"] = "list"
    data["path_img"] = image
    data["path_bg"] = background
    data["path_ft_title"] = "./develop_env/font3d/3d-noise.ttf"
    data["path_ft_song"] = "./develop_env/font2d/gunplay.ttf"
    data["data_list"] = data_text
    data['size_title'] = 60
    data['size_song'] = 22

    return data


def create_grayscale_data(path_ob):
    if os.path.isdir(path_ob) is False:
        print(f"Not found folder object {path_ob}")
        return False

    list_ob = os.listdir(path_ob)

    # Get image
    image = f"{path_ob}/{list_ob[random.randint(0, len(list_ob) - 1)]}"

    data = dict()

    data["style"] = "grayscale"
    data["path_img"] = image

    return data


def create_change_data(path_ob, path_bg):
    if os.path.isdir(path_ob) is False:
        print(f"Not found folder object {path_ob}")
        return False
    if os.path.isdir(path_bg) is False:
        print(f"Not found folder background {path_bg}")
        return False

    data = dict()
    list_ob = os.listdir(path_ob)
    list_bg = os.listdir(path_bg)

    # Get background
    background = f"{path_bg}/{list_bg[random.randint(0, len(list_bg)) - 1]}"
    image = f"{path_ob}/{list_ob[random.randint(0, len(list_ob) - 1)]}"
    print(image)

    data["style"] = "crop"
    data["path_ob"] = image
    data["path_bg"] = background

    return data


def create_blur_data(path_ob):
    if os.path.isdir(path_ob) is False:
        print(f"Not found folder object {path_ob}")
        return False

    data = dict()

    list_ob = os.listdir(path_ob)

    # Get image path
    image = f"{path_ob}/{list_ob[random.randint(0, len(list_ob) - 1)]}"

    data["style"] = "blurring"
    data["path_img"] = image

    return data


def create_crop_data(path_ob):
    if os.path.isdir(path_ob) is False:
        print(f"Not found folder object {path_ob}")
        return False

    data = dict()
    list_index = []
    count = 0
    num_img = random.randint(2, 4)
    list_ob = os.listdir(path_ob)
    list_img = []
    list_font = os.listdir("./develop_env/font3d")

    while count < num_img:
        index = random.randint(0, len(list_ob) - 1)
        if index not in list_index:
            list_img.append(f'{path_ob}/{list_ob[index]}')
            count += 1
            list_index.append(index)

    data['font'] = f"./develop_env/font3d/{list_font[random.randint(0,len(list_font)-1)]}"
    data['text'] = "This program for test case"

    data["style"] = "crop"
    data["list_img"] = list_img

    return data

def create_render_data():
    data = dict()
    list_img_origin = ["./develop_env/object/pexels-ali-pazani-2681751.jpg",
                       "./develop_env/object/pexels-ali-pazani-2887718.jpg"]

    list_img_ob = ["./develop_env/template_render/ex7/ob_1.png",
                   "./develop_env/template_render/ex7/ob_2.png"]

    img_txt = "./develop_env/template_render/ex7/text.png"

    frame_template = "./develop_env/template_render/ex7/frame.png"
    path_model = 'model/u2net_human_seg.pth'
    path_font = './develop_env/font2d/ACaslonPro-Bold.otf'
    path_font_singer = "develop_env/font2d/AGaramondPro-Italic.otf"
    path_out = "./develop_env"
    try:
        with open('./develop_env/data/list_song.json') as json_file:
            data = json.load(json_file)
            print(data)
    except ValueError as error:
        print(error)
    data["style"] = "template_generation_multi"
    data['list_path_img_origin'] = list_img_origin
    data['path_img_txt'] = img_txt
    data['list_path_img_ob'] = list_img_ob
    data['_img_frame'] = frame_template
    data['path_ft_singer'] = path_font_singer
    data['path_ft_song'] = path_font
    data['data_list'] = data
    data['size_txt'] = 25

    return data


if __name__ == '__main__':
    path_object = './develop_env/object'
    path_background = './develop_env/background'
    path_model = 'model/u2net_human_seg.pth'
    net = load_model(path_model)
    # net = load_model('./image_processing/lib/object_segment/u2net.pth')
    path_output = "./develop_env/output"
    count = 0
    mode = 6
    data = False
    i = 1
    while i == 1:
        i = 2
        # mode = random.randint(1, 6)
        if mode == 1:
            data = create_crop_data(path_object)
        elif mode == 2:
            data = create_list_data(path_object, path_background)
        # elif mode == 3:
        #     data = create_blur_data(path_object)
        # elif mode == 4:
        #     data = create_change_data(path_object, path_background)
        # elif mode == 5:
        #     data = create_grayscale_data(path_object)
        # else:
        #     data = create_split_data(path_object, path_background)
        # data = create_list_data()
        elif mode == 6:
            data = create_render_data()
        if data is False:
            continue
        path, num = image_processing(data, net, show_img=True, path_output=path_output)
        print(f"Output is {path}")
        if path is False:
            continue
        im = Image.open(path)
        print(f"The output image was save at {path}")
        im.show()
        # count += 1
        #
        # if count == 100:
        #     break
