#!/usr/bin/env python

# fix building inside a virtualbox VM
# http://bugs.python.org/issue8876#msg208792
try:
    import os
    del os.link
except:
    pass

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# get our version but don't import it
# or we'll need our dependencies already installed
# https://github.com/todddeluca/happybase/commit/63573cdaefe3a2b98ece87e19d9ceb18f00bc0d9
with open('omgl/version.py', 'r') as f:
    exec(f.read())

setup(
    name='omgl',
    version=__version__,
    description='Pythonic OpenGL Bindings',
    license='BSD',
    author='Adam Griffiths',
    url='https://github.com/adamlwgriffiths/omgl',
    install_requires=[
        # due to bugs in 1.9, we MUST use 1.8
        # https://github.com/numpy/numpy/issues/5224
        'numpy==1.8.2',
        'pyopengl',
        'pillow',
    ],
    tests_require=[],
    extras_require={
        'cyglfw3': ['cyglfw3'],
        'accelerate': ['pyopengl-accelerate'],
        'pyrr': ['pyrr'],
    },
    platforms=['any'],
    packages=[
        'omgl',
        'omgl.buffer',
        'omgl.mesh',
        'omgl.pipeline',
        'omgl.shader',
        'omgl.texture',
    ],
    classifiers=[
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'License :: OSI Approved :: BSD License',
        'Topic :: Multimedia :: Graphics',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
