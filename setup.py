from setuptools import setup

__author__ = 'Cash Costello'
__email__ = 'cash.costello@jhuapl.edu'
__version__ = '0.1.0.dev'

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
        'faker', 'langdetect',
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
