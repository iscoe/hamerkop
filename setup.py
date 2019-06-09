import re
from setuptools import setup

__author__ = 'Cash Costello'
__email__ = 'cash.costello@jhuapl.edu'

with open('hamerkop/__init__.py', 'r') as fp:
    __version__ = re.search(r"__version__ = \'(.*?)\'", fp.read()).group(1)

setup(
    name='hamerkop',
    version=__version__,
    description='Entity linking framework',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author=__author__,
    author_email=__email__,
    url='https://github.com/iscoe/hamerkop',
    license='Apache License 2.0',
    packages=['hamerkop'],
    install_requires=[
        'langdetect',
    ],
    python_requires='>=3.5',
    keywords=['knowledge base', 'coreference', 'entity linking'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Scientific/Engineering',
        'Topic :: Text Processing',
    ],
)
