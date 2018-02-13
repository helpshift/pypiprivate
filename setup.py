import re
import ast

from setuptools import setup


_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('pypiprivate/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(f.read().decode('utf-8')).group(1)))


setup(
    name='pypiprivate',
    version=version,
    author='Vineet Naik',
    author_email='vineet@helpshift.com',
    url='http://helpshift.com',
    license='Proprietary',
    description='Private package management tool for Python projects',
    install_requires=['Jinja2==2.10.0',
                      'boto3==1.5.27'],
    packages=['pypiprivate'],
    entry_points={
        'console_scripts': [
            'pypi-private = pypiprivate.cli:main'
        ]
    }
)
