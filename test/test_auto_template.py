from PIL import Image
from image_processing import image_processing, load_model

import os
import json
import random


def test_template_auto(net, path_ob_test, path_bg_test, path_output, show_img=False):

    if os.path.isdir(path_bg_test) is False:
        print(f"{path_bg_test} is not exits")
        return False

    if os.path.isdir(path_ob_test) is False:
        print(f"{path_ob_test} is not exits")
        return False

    secure_random = random.SystemRandom()
    list_bgs = os.listdir(path_bg_test)

    if len(list_bgs) == 0:
        print(f"{path_bg_test} have no file")
        return False

    bg_img = secure_random.choice(list_bgs)
    bg_img_path = f"{path_bg_test}/{bg_img}"

    secure_random = random.SystemRandom()
    list_obs = os.listdir(path_ob_test)

    if len(list_obs) == 0:
        print(f"{path_ob_test} have no file")
        return False

    data = dict()

    # Get object image
    ob_img = secure_random.choice(list_obs)
    ob_img_path = f"{path_ob_test}/{ob_img}"

    # Get position object
    position_list = ["left", "right"]
    position = secure_random.choice(position_list)

    # Get collum_mode
    list_collum_mode = [1, 2, "title_style"]
    if position == "center":
        collum_mode = 2
    else:
        collum_mode = secure_random.choice(list_collum_mode)

    collum_mode = "title_style"

    # Get data_list
    try:
        with open('./develop_env/data/data_test.json') as json_file:
            data_list = json.load(json_file)

    except ValueError as error:
        print(error)

    list_align_values = ["right", "center", "left"]
    data_list["align"] = secure_random.choice(list_align_values)

    if collum_mode == 1:
        list_mode_values = ["line", "no_line", "singer"]
        data_list["mode"] = secure_random.choice(list_mode_values)

    list_titles = ["Jesús Adrián Romero",
                   "La Mejor Musica \nCristiana 2021 Colección"]

    title = secure_random.choice(list_titles)
    data_list["title"] = title

    data["style"] = 'auto'
    data['path_img_origin'] = ob_img_path
    data['background'] = bg_img_path
    data['data_list'] = data_list
    data['collum_mode'] = collum_mode
    data['ob_position'] = position

    result = image_processing(data, net, path_output, show_img=show_img)

    return result


if __name__ == "__main__":

    model = "./model/u2net.pth"
    net = load_model(model)

    path_ob_test = "./develop_env/object_test"
    path_bg_test = "./develop_env/background"
    path_output = "./develop_env/output_test"

    count = 0
    while count < 200:
        count += 1
        result = test_template_auto(net, path_ob_test, path_bg_test, path_output, show_img=False)
        print(result)
