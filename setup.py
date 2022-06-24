import setuptools
from setuptools import setup, find_packages

setuptools.setup(
    name="image_processing",
    version="2.4.15",
    script="Image_process",
    author="hai-nd",
    author_email="haind.ee.094@hotmail.com",
    descreption="This package to image processing",
    long_description_content_type="text/markdown",
    url="https://git.vfast.live/VFAST/SUNNY_ECO_IMG_AI",
    packages=find_packages(),
    classifiers=[
        "Programming language :: Python :: 3",
        "LICENSE :: OSI Approved :: MIT LICENSE",
        "Operating system :: OS Independent",
    ],
    entry_points={
            "console_scripts": [
                "myscript = image_processing.__main__:main",
            ]
    }
)