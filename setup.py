import os
from setuptools import setup


def localopen(fname):
    return open(os.path.join(os.path.dirname(__file__), fname))


setup(
    name='pymps',
    version='0.1',
    description='Libary to parse fixed-format MPS files.',
    author='Constantino Schillebeeckx',
    author_email='constantino@simplerose.com',
    py_modules=['pymps'],
    include_package_data=True,
    zip_safe=False,
    keywords=['netlib', 'linear programming'],
    url='https://github.com/simpleroseinc/pymps',
    long_description=localopen('README.md').read(),
    install_requires=['numpy', 'pandas'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: Other/Proprietary License',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ]
)
