from setuptools import setup
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='cbpi4-fermenter-autorestart',
    version='1.0.13',
    description='CraftBeerPi4 Fermenter Hysteresis with Auto Resume State After Reboot',
    author='Pierre',
    author_email='',
    url='',
    license='GPLv3',
    include_package_data=True,
    packages=['cbpi4_fermenter_autorestart'],
    install_requires=[],
    entry_points={
        'cbpi4.plugin': [
            'cbpi4_fermenter_autorestart = cbpi4_fermenter_autorestart',
        ],
    },
    long_description=long_description,
    long_description_content_type='text/markdown',
)
