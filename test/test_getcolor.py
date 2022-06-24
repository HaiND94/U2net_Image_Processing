from PIL import Image, ImageColor

# img_url = "./develop_env/background/6.jpg"
img_url = "./develop_env/background/1467807.jpg"


def get_main_color(file):
    img = Image.open(file)
    colors = img.getcolors(256)
    print(colors)
    max_occurence, most_present = 0, 0
    try:
        for c in colors:
            if c[0] > max_occurence:
                (max_occurence, most_present) = c
        return most_present
    except TypeError:
        raise Exception("Too many colors in the image")


if __name__ == "__main__":
    print(get_main_color(img_url))

