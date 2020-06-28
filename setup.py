import re
import ast

from setuptools import setup


_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('pypiprivate/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(f.read().decode('utf-8')).group(1)))


with open('./README.rst') as f:
    long_desc = f.read()


extras_require = {
    'azure': [
        'azure-storage-blob==12.2.0'
    ]
}


setup(
    name='pypiprivate',
    version=version,
    author='Vineet Naik',
    author_email='vineet@helpshift.com',
    url='https://github.com/helpshift/pypiprivate',
    license='MIT License',
    description='Private package management tool for Python projects',
    long_description=long_desc,
    install_requires=['setuptools>=36.0.0',
                      'Jinja2==2.10.0',
                      'boto3==1.5.27'],
    extras_require=extras_require,
    packages=['pypiprivate'],
    entry_points={
        'console_scripts': [
            'pypi-private = pypiprivate.cli:main'
        ]
    },
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.6',
    ]
)
