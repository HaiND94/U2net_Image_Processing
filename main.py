import face_recognition
from PIL import Image, ImageFilter

im = Image.open("./develop_env/images/error.jpg")
im.show()

image = im.copy()
image = image.convert("L")

# Detecting Edges on the Image using the argument ImageFilter.FIND_EDGES
image = image.filter(ImageFilter.FIND_EDGES)
image = image.point(lambda x: 0 if x < 100 else 255, '1')
box = image.getbbox()
print(box)

image.show()

im = im.crop(box)
im.show()