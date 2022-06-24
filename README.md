# Image processing use deep learning

Use for create image use deep learning. This code have 7 function
- Background blurring
- Background change 
- Background grayscale
- Background change for multi object
- Crop image follow face
- Create image follow template

[![PyPI](https://img.shields.io/pypi/v/face_recognition.svg)](https://pypi.python.org/pypi/face_recognition)
[![Build Status](https://github.com/ageitgey/face_recognition/workflows/CI/badge.svg?branch=master&event=push)](https://github.com/ageitgey/face_recognition/actions?query=workflow%3ACI)
[![Documentation Status](https://readthedocs.org/projects/face-recognition/badge/?version=latest)](http://face-recognition.readthedocs.io/en/latest/?badge=latest)

<a href="https://opencv.org/courses/">
<p align="center"> 
<img src="https://www.learnopencv.com/wp-content/uploads/2020/04/AI-Courses-By-OpenCV-Github.png">
</p>
</a>

####Requirements
  * Python 3.3+
  * macOS or Linux

####Manual install environment
    # using pip
        * pip install -r requirements.txt

    # using Conda
        * conda create --name <env_name> --file requirements.txt

## Features
####Background blurring

```python

from image_processing.lib import background_blurring

# Set your image path
img_path = 'develop_env/images/blur/girl.png'

background_blurring.segment(img_path, show_orig=False)
```
####Background change

```python

from image_processing import background_change

# Set your path image 
img_path = 'develop_env/images/blur/girl.png'
background_path = 'develop_env/images/change/background-building.png'

background_change.segment(img_path, background_path, show_orig=True)
```
####Background grayscale

```python

from image_processing import background_grayscale

# Set your image path
img_path = 'develop_env/images/greyscale/boat.png'

background_grayscale.segment(img_path, show_orig=False)
```
####Background change with multi object

```python
from image_processing import background_change_multi

# Set path background image
path_background = 'develop_env/images/background/forest.png'
# Set path folder where is store object image which we need to crop
path_ground = 'develop_env/images/task'

background_change_multi.segment(path_ground, path_background, show_orig=False)
```
####Crop object from images and merge objects into one image

```python

from image_processing import crop_image

# Path to image
# The image path contains the object
path_folder = 'develop_env/images/singer'
# The output folder 
path_output = 'develop_env/images/ouput'

# Crop
crop_image.crop_multi_image(path_source=path_folder, path_create=path_output, show_img=True)
```
####Create image follow template

```python

from image_processing import template

# The image path contain background image
path_background = 'develop_env/images/background/background.jpg'
# Tha folder path where contain object image
path_ground = 'develop_env/images/task'

template.segment(path_ground, path_background, add_border=True, show_orig=False)
```