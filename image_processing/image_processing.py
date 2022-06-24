import json
import random
import os

try:
    from lib import blurring, grayscale, template_list, crop_multi_image, \
        change, load_model, swap_object, template_crop, template_generation, \
        template_generation_multi, template_generation_worship, top_songs, auto, \
        top_songs_no_edge, template_fl_image
except:
    from .lib import blurring, grayscale, template_list, crop_multi_image, \
        change, load_model, swap_object, template_crop, template_generation,\
        template_generation_multi, template_generation_worship, top_songs, auto, \
        top_songs_no_edge, template_fl_image


def image_processing(data, net, path_output, show_img=False):
    result = dict()
    result["status"] = "error"
    result["content"] = ''
    result["data"] = []
    result["image_false"] = ''

    if os.path.isdir(path_output) is False:
        print(f"Cannot find {path_output}")
        result["content"] = f"Cannot find {path_output}"
        return result

    _template = ['blurring', 'change', 'grayscale',
                 'crop', 'split', 'list', 'template_crop',
                 'template_generation', "template_generation_multi",
                 'template_generation_worship', 'top_songs', 'auto',
                 'top_songs_no_edge', 'template_fl_image']

    try:
        template = data["style"]
        if template not in _template:
            print(f"Data style not True, must be in {_template}, Received {template}")
            result["content"] = f"Data style not True, must be in {_template}, Received {template}"
            return result

    except Exception as error:
        print(error)
        result["content"] = error
        return result

    if template == 'blurring':
        try:
            path_img = data['path_img']
            path_ft_title = data['path_ft_title']
            path_ft_song = data['path_ft_song']
            data_list = data['data_list']
            size_title = data['size_title']
            size_song = data['size_song']

        except Exception as error:
            print("Can not convert data to input format\n")
            print(error)
            result["content"] = error
            return result

        mode = ['left', 'right']

        path = blurring(path_img, net, path_output_folder=path_output, path_font_title=path_ft_title,
                        path_font_song=path_ft_song,
                        size_text=size_song, size_title=size_title,
                        js_text=data_list, align=mode[random.randint(0, 1)],
                        show_img=show_img)
        if path is False:
            result["content"] = "Can not create image follow require"
            return result

        result["data"] = path
        result["status"] = "success"

    elif template == 'change':
        try:
            path_img = data['path_img']
            path_bg = data['path_bg']
            path_ft_title = data['path_ft_title']
            path_ft_song = data['path_ft_song']
            data_list = data['data_list']
            size_title = data['size_title']
            size_song = data['size_song']

        except Exception as error:
            print("Can not convert data to input format\n")
            print(error)
            result["content"] = error
            return result

        mode = ['left', 'right']

        path = swap_object(img=path_img, bg=path_bg, path_output=path_output,
                           path_font_title=path_ft_title, path_font_song=path_ft_song,
                           js_txt=data_list, size_text=size_song, size_title=size_title,
                           align=mode[random.randint(0, 1)], show_img=show_img)
        if path is False:
            result["content"] = "Can not create image follow require"
            return result

        result["data"] = path
        result["status"] = "success"

    elif template == 'grayscale':
        try:
            img_origin = data['path_img_origin']
            data_list = data['data_list']
            col_mod = data['collum_mode']

        except Exception as error:
            print("Can not convert data to input format\n")
            print(error)
            result["content"] = error
            return result

        try:
            path = grayscale(net, path=img_origin,
                             path_out=path_output,
                             collum_mode=col_mod,
                             js_txt=data_list, debug=show_img)
            result = path

        except Exception as error:
            print(error)
            result["content"] = error
            return result

    elif template == 'template_fl_image':
        try:
            img_origin = data['path_img_origin']
            data_list = data['data_list']
            col_mod = data['collum_mode']

        except Exception as error:
            print("Can not convert data to input format\n")
            print(error)
            result["content"] = error
            return result

        try:
            path = template_fl_image(net, path=img_origin,
                                     path_out=path_output,
                                     collum_mode=col_mod,
                                     js_txt=data_list, debug=show_img)
            result = path

        except Exception as error:
            print(error)
            result["content"] = error
            return result

    elif template == 'crop':
        try:
            list_img = data['list_img']
            path_font = data['font']
            _text = data['text']
            size_title = data["size_title"]

            # path_create = data['path_create']
        except Exception as error:
            print("Can not convert data to input format\n")
            print(error)
            result["content"] = error
            return result

        try:
            path = crop_multi_image(list_img, path_output=path_output,
                                    path_font_title=path_font, size_txt=size_title,
                                    text=_text, show_img=show_img)
            if path is False:
                result["content"] = "Can not create image follow require"
                return result

            result["data"] = path
            result["status"] = "success"

        except Exception as error:
            result["content"] = error
            return result

    elif template == 'template_crop':
        try:
            list_img = data['list_img']
            path_font = data['font']
            _text = data['text']
            size_title = data["size_title"]

            # path_create = data['path_create']
        except Exception as error:
            print("Can not convert data to input format\n")
            result["content"] = error
            return result

        try:
            path = template_crop(list_img, path_output=path_output,
                                 path_font_title=path_font, size_txt=size_title,
                                 text=_text, show_img=show_img)
            if path is False:
                result["content"] = "Can not create image follow require"
                return result
            result["data"] = path
            result["status"] = "success"

        except Exception as error:
            print(error)
            result["content"] = error
            return result

    elif template == 'list':
        try:
            path_img = data['path_img']
            path_bg = data['path_bg']
            path_ft_title = data['path_ft_title']
            path_ft_song = data['path_ft_song']
            data_list = data['data_list']
            size_title = data['size_title']
            size_song = data['size_song']

        except Exception as error:
            print("Can not convert data to input format\n")
            print(error)
            result["content"] = error
            return result

        mode = ['left', 'right']
        try:
            path = template_list(img=path_img, bg=path_bg,
                                 path_font_title=path_ft_title, path_font_song=path_ft_song,
                                 js_txt=data_list, net=net,
                                 size_text=size_song, size_title=size_title,
                                 path_output=path_output, align=mode[random.randint(0, 1)],
                                 add_border=False, show_img=show_img)
            if path is False:
                result["content"] = "Can not create image follow require"
                return result

            result["data"] = path
            result["status"] = "success"

        except Exception as error:
            result["content"] = error
            return result

    elif template == "template_generation_multi":
        try:
            img_origin = data['list_path_img_origin']
            img_txt = data['path_img_txt']
            img_ob = data['list_path_img_ob']
            img_frame = data['img_frame']
            data_list = data['data_list']
            col_mod = data['collum_mode']

        except Exception as error:
            print("Can not convert data to input format\n")
            print(error)
            return False
        try:
            path = template_generation_multi(net, img_origin, img_frame,
                                             img_ob, img_txt,
                                             path_output,
                                             collum_mode=col_mod,
                                             js_txt=data_list, debug=show_img)
            result = path
        except Exception as error:
            result["content"] = error
            return result

    elif template == "template_generation_worship":

        try:
            img_txt = data['path_img_txt']
            data_list = data['data_list']
            img_frame = data['img_frame']
            col_mod = data['collum_mode']

        except Exception as error:
            print("Can not convert data to input format\n")
            print(error)
            result["content"] = error
            return result
        try:
            path = template_generation_worship(img_frame, img_txt,
                                               path_out=path_output,
                                               collum_mode=col_mod,
                                               js_txt=data_list, debug=show_img)
            result = path
        except Exception as error:
            print(error)
            result["content"] = error
            return result

    elif template == "top_songs":
        try:
            img_origin = data['list_path_img_origin']
            img_txt = data['path_img_txt']
            img_ob = data['list_path_img_ob']
            img_frame = data['img_frame']
            data_list = data['data_list']
            col_mod = data['collum_mode']

        except Exception as error:
            print("Can not convert data to input format\n")
            print(error)
            result["content"] = error
            return result

        try:
            path = top_songs(net, list_img_origin=img_origin, frame_template=img_frame,
                             list_img_ob=img_ob, img_txt=img_txt, path_out=path_output,
                             js_txt=data_list, collum_mode=col_mod, debug=show_img)
            result = path
        except Exception as error:
            print(error)
            result["content"] = error
            return result

    elif template == "auto":
        try:
            img_origin = data['path_img_origin']
            img_background = data['background']
            data_list = data['data_list']
            col_mod = data['collum_mode']
            ob_position = data['ob_position']

        except Exception as error:
            print("Can not convert data to input format\n")
            print(error)
            result["content"] = error
            return result

        try:
            path = auto(net, img_origin=img_origin,
                        img_background=img_background,
                        ob_position=ob_position,
                        path_out=path_output,
                        js_txt=data_list, collum_mode=col_mod, debug=show_img)
            result = path
        except Exception as error:
            print(error)
            result["content"] = error
            return result

    elif template == "top_songs_no_edge":
        try:
            img_origin = data['list_path_img_origin']
            img_txt = data['path_img_txt']
            img_ob = data['list_path_img_ob']
            img_frame = data['img_frame']
            data_list = data['data_list']
            col_mod = data['collum_mode']

        except Exception as error:
            print("Can not convert data to input format\n")
            print(error)
            result["content"] = error
            return result

        try:
            path = top_songs_no_edge(net, list_img_origin=img_origin, frame_template=img_frame,
                                     list_img_ob=img_ob, img_txt=img_txt, path_out=path_output,
                                     js_txt=data_list, collum_mode=col_mod, debug=show_img)
            result = path
        except Exception as error:
            print(error)
            result["content"] = error
            return result

    else:
        print("Data input not right!")
        result["content"] = "Data input not right!"
        return result

    if path is False:
        result["content"] = "Can not create image follow request"
        return result

    return result


if __name__ == '__main__':

    test_case = 'blurring'

    path_font_title = './develop_env/font3d'
    path_font_song = './develop_env/font2d'
    data = {}

    if test_case == 'split':
        try:
            with open('./develop_env/data/split.json') as json_file:
                data = json.load(json_file)
                # print(data)
        except ValueError as error:
            print(error)

    elif test_case == 'change':
        try:
            with open('./develop_env/data/change.json') as json_file:
                data = json.load(json_file)
                # print(data)
        except ValueError as error:
            print(error)

    elif test_case == 'blurring':
        try:
            with open('./develop_env/data/blurring.json') as json_file:
                data = json.load(json_file)
                # print(data)
        except ValueError as error:
            print(error)

    elif test_case == 'crop':
        try:
            with open('./develop_env/data/crop.json') as json_file:
                data = json.load(json_file)
                # print(data)
        except ValueError as error:
            print(error)

    elif test_case == 'list':
        try:
            with open('./develop_env/data/list.json') as json_file:
                data = json.load(json_file)
                # print(data)
        except ValueError as error:
            print(error)

    elif test_case == 'grayscale':
        try:
            with open('./develop_env/data/grayscale.json') as json_file:
                data = json.load(json_file)
        except ValueError as error:
            print(error)

    else:
        print('Test case not right!')

    path_model = './image_processing/lib/object_segment/u2net.pth'
    text = "TOP 2020"

    # print(img.size)

    net = load_model(path_model, model_name='u2net')

    print(image_processing(data, net))
